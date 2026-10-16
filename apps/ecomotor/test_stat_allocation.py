"""Asignación S7-A con parámetros exclusivamente ficticios."""

from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import IntegrityError, OperationalError, connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config
from .admin import ReadOnlySuperuserAdmin
from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, STAT_ATTRIBUTES,
    Specialization, StatAllocationEvent, UserSpecializationProgress, XPEvent,
)
from .progress_queries import get_progress_overview, list_progress_history
from .stat_allocation import (
    AllocationConflictError, AllocationDatabaseError, AllocationOverflowError,
    InconsistentAllocationStateError, IneligibleStageError, InsufficientPointsError,
    InvalidAllocationConfigurationError, InvalidAllocationKeyError,
    InvalidAllocationProfileError, InvalidAttributeError, InvalidPointsError, allocate_stat_points,
)
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


class StatAllocationTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="s7-test-user")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)
        grant_historical_xp(self.profile, 102, "s7-test-reach-actual")
        self.profile.refresh_from_db()
        self.stats = CharacterStats.objects.get(profile=self.profile)
        UserProfileBank.objects.create(user=self.profile.user)

    def snapshot(self):
        return [list(m.objects.order_by("pk").values()) for m in (
            get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
            XPEvent, EvolutionEvent, UserSpecializationProgress, Specialization,
            EvolutionStage, LevelThreshold, StatAllocationEvent,
        )]

    def reject(self, error, attribute="atk", points=2, key="s7-rejected", profile=None):
        before = self.snapshot()
        with self.assertRaises(error):
            allocate_stat_points(self.profile if profile is None else profile, attribute, points, key)
        self.assertEqual(before, self.snapshot())

    def test_six_attributes_exact_one_to_one_without_other_changes(self):
        for attribute in STAT_ATTRIBUTES:
            with self.subTest(attribute=attribute):
                self.stats.refresh_from_db()
                before = {name: getattr(self.stats, name) for name in STAT_ATTRIBUTES}
                balance = self.stats.available_points
                result = allocate_stat_points(self.profile, attribute, 1, "s7-" + attribute)
                self.stats.refresh_from_db()
                self.assertFalse(result.replayed)
                self.assertEqual(self.stats.available_points, balance - 1)
                self.assertEqual(result.attribute_before, before[attribute])
                self.assertEqual(result.attribute_after, before[attribute] + 1)
                self.assertEqual(result.increase_applied, 1)
                for name in STAT_ATTRIBUTES:
                    self.assertEqual(getattr(self.stats, name), before[name] + (name == attribute))

    def test_exact_arrival_to_actual_is_eligible_and_initial_stats_not_validated(self):
        self.assertIsNone(XP_CONFIGURATION.atk)
        self.assertEqual(self.profile.historical_xp_total, 102)
        result = allocate_stat_points(self.profile, "atk", 3, "s7-exact")
        self.assertEqual((result.available_points_before, result.available_points_after), (14, 11))
        self.assertEqual(result.stage_code_at_allocation, XP_CONFIGURATION.ordered_stage_codes[6])

    def test_previous_stage_not_eligible(self):
        other = create_xp_profile(username="s7-prior")
        self.reject(IneligibleStageError, profile=other)

    def test_missing_or_invalid_configuration(self):
        for config in (None, {}, replace(XP_CONFIGURATION, ordered_stage_codes=("same",) * 7)):
            with self.subTest(config=config), patch.object(initialization_config, "INITIAL_CONFIGURATION", config):
                self.reject(InvalidAllocationConfigurationError)

    def test_incomplete_stage_catalog(self):
        # Evitar PROTECT: eliminar una etapa de un catálogo nuevo sin evoluciones.
        EvolutionEvent.objects.all().delete()
        EvolutionStage.objects.filter(ordinal=3).delete()
        self.reject(InvalidAllocationConfigurationError)

    def test_invalid_stage_thresholds(self):
        EvolutionStage.objects.filter(ordinal=7).update(minimum_xp=1)
        self.reject(InvalidAllocationConfigurationError)

    def test_stage_mismatch_is_inconsistency(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="wrong-test-code")
        self.reject(InconsistentAllocationStateError)

    def test_no_level_catalog_dependency(self):
        LevelThreshold.objects.all().delete()
        self.assertFalse(allocate_stat_points(self.profile, "atk", 1, "s7-no-levels").replayed)

    def test_invalid_and_nonexistent_profile(self):
        for profile in (None, UserProfileEcomotor(), object()):
            with self.assertRaises(InvalidAllocationProfileError):
                allocate_stat_points(profile, "atk", 1, "s7-invalid")
        missing = create_xp_profile(username="s7-missing")
        pk = missing.pk
        missing.delete()
        missing.pk = pk
        self.reject(InvalidAllocationProfileError, profile=missing)

    def test_partial_profile_rejected(self):
        self.stats.delete()
        self.reject(InconsistentAllocationStateError)

    def test_legacy_fractional_stat_rejected_without_conversion(self):
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_characterstats SET atk=1.5 WHERE id=%s", [self.stats.pk])
        self.reject(InconsistentAllocationStateError)

    def test_invalid_attribute_names(self):
        for value in ("ATK", "DEF", "INT", "available_points", "profile__id", "", None, True, []):
            with self.subTest(value=value):
                self.reject(InvalidAttributeError, attribute=value)

    def test_invalid_points(self):
        for value in (0, -1, True, False, 1.5, "2", None, 2**80):
            with self.subTest(value=value):
                self.reject(InvalidPointsError, points=value)

    def test_invalid_keys(self):
        for value in ("", "x" * 256, None, 1, True):
            with self.subTest(value=value):
                self.reject(InvalidAllocationKeyError, key=value)

    def test_key_not_normalized(self):
        result = allocate_stat_points(self.profile, "atk", 1, " key with spaces ")
        self.assertEqual(result.operation_key, " key with spaces ")

    def test_insufficient_balance(self):
        self.reject(InsufficientPointsError, points=15)

    def test_spend_exact_balance(self):
        result = allocate_stat_points(self.profile, "atk", 14, "s7-all")
        self.assertEqual(result.available_points_after, 0)

    def test_signed_attribute_supported(self):
        CharacterStats.objects.filter(pk=self.stats.pk).update(def_stat=-5)
        result = allocate_stat_points(self.profile, "def_stat", 2, "s7-negative")
        self.assertEqual((result.attribute_before, result.attribute_after), (-5, -3))

    def test_attribute_technical_limit_and_overflow(self):
        upper = connection.ops.integer_field_range("IntegerField")[1]
        CharacterStats.objects.filter(pk=self.stats.pk).update(atk=upper - 1)
        self.assertEqual(allocate_stat_points(self.profile, "atk", 1, "s7-limit").attribute_after, upper)
        self.reject(AllocationOverflowError)

    def test_event_snapshot_overflow_checked_before_write(self):
        # Simula backend cuyo campo de snapshot tiene rango menor al atributo.
        original = connection.ops.integer_field_range
        # Limitar solo el snapshot, sin cambiar los rangos de ordinales o saldo.
        field = StatAllocationEvent._meta.get_field("attribute_after")
        with patch.object(field, "get_internal_type", return_value="TestSnapshotInteger"), \
                patch.object(connection.ops, "integer_field_range", side_effect=lambda kind:
                             (0, 3) if kind == "TestSnapshotInteger" else original(kind)):
            self.reject(AllocationOverflowError, points=2)

    def test_replay_is_original_frozen_and_has_no_writes(self):
        first = allocate_stat_points(self.profile, "atk", 2, "s7-replay")
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            replay = allocate_stat_points(self.profile, "atk", 2, "s7-replay")
        self.assertEqual(replace(first, replayed=True), replay)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(any(q["sql"].upper().startswith(("INSERT", "UPDATE", "DELETE")) for q in queries))
        with self.assertRaises(FrozenInstanceError):
            replay.points_spent = 3

    def test_conflicts_by_attribute_or_quantity(self):
        allocate_stat_points(self.profile, "atk", 2, "s7-key")
        self.reject(AllocationConflictError, attribute="def_stat", key="s7-key")
        self.reject(AllocationConflictError, points=3, key="s7-key")

    def test_replay_after_allocation_xp_and_configuration_retired(self):
        first = allocate_stat_points(self.profile, "atk", 2, "s7-old")
        allocate_stat_points(self.profile, "atk", 3, "s7-new")
        grant_historical_xp(self.profile, 17, "s7-later-xp")
        for config in (None, replace(XP_CONFIGURATION, ordered_stage_codes=tuple(f"changed-{i}" for i in range(7)))):
            with patch.object(initialization_config, "INITIAL_CONFIGURATION", config):
                replay = allocate_stat_points(self.profile, "atk", 2, "s7-old")
            self.assertEqual(replace(first, replayed=True), replay)

    def test_corrupt_event_structural_code_rejected(self):
        first = allocate_stat_points(self.profile, "atk", 2, "s7-corrupt")
        StatAllocationEvent.objects.filter(pk=first.allocation_event_id).update(stage_code_at_allocation="x" * 33)
        self.reject(InconsistentAllocationStateError, key="s7-corrupt")

    def test_fractional_historical_snapshots_rejected(self):
        first = allocate_stat_points(self.profile, "atk", 2, "s7-fraction")
        # Contraejemplo aritméticamente coherente aceptado por SQLite, no por servicio.
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_statallocationevent SET attribute_before=2.5, attribute_after=4.5 WHERE id=%s",
                           [first.allocation_event_id])
        self.reject(InconsistentAllocationStateError, key="s7-fraction")

    def test_corrupt_arithmetic_history_is_rejected_not_repaired(self):
        first = allocate_stat_points(self.profile, "atk", 2, "s7-broken-history")
        # Solo BD de pruebas: simula corrupción externa que el ORM no puede insertar.
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA ignore_check_constraints = ON")
            try:
                cursor.execute("UPDATE ecomotor_statallocationevent SET increase_applied=3 WHERE id=%s",
                               [first.allocation_event_id])
            finally:
                cursor.execute("PRAGMA ignore_check_constraints = OFF")
        self.reject(InconsistentAllocationStateError, key="s7-broken-history")

    def test_structurally_invalid_profile_rejected(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="x" * 33)
        self.reject(InconsistentAllocationStateError)

    def test_foreign_key_required_and_nonexistent_profile_rejected_by_database(self):
        for profile_id in (None, self.profile.pk + 10000):
            with self.subTest(profile_id=profile_id), self.assertRaises(IntegrityError), transaction.atomic():
                values = self.event_values()
                del values["profile"]
                StatAllocationEvent.objects.create(**values, profile_id=profile_id)
                connection.check_constraints()

    def test_cascade_is_provisional_and_no_automatic_events_created(self):
        other = create_xp_profile(username="s7-cascade")
        self.assertFalse(StatAllocationEvent.objects.filter(profile=other).exists())
        grant_historical_xp(other, 102, "s7-cascade-actual")
        allocate_stat_points(other, "atk", 1, "s7-cascade")
        other.delete()
        self.assertFalse(StatAllocationEvent.objects.exists())

    def event_values(self):
        return dict(profile=self.profile, operation_key="s7-direct", attribute="atk", points_spent=2,
                    increase_applied=2, available_points_before=14, available_points_after=12,
                    attribute_before=-3, attribute_after=-1,
                    stage_code_at_allocation=XP_CONFIGURATION.ordered_stage_codes[6])

    def test_real_database_constraints(self):
        invalid = ({"operation_key": ""}, {"attribute": "ATK"}, {"points_spent": 0},
                   {"points_spent": -1}, {"increase_applied": 0}, {"increase_applied": 3},
                   {"available_points_before": 15}, {"available_points_after": -1},
                   {"attribute_after": 9}, {"stage_code_at_allocation": ""})
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(IntegrityError), transaction.atomic():
                StatAllocationEvent.objects.create(**(self.event_values() | changes))

    def test_unique_per_profile_and_same_key_other_profile(self):
        StatAllocationEvent.objects.create(**self.event_values())
        with self.assertRaises(IntegrityError), transaction.atomic():
            StatAllocationEvent.objects.create(**self.event_values())
        other = create_xp_profile(username="s7-other")
        grant_historical_xp(other, 102, "s7-other-actual")
        self.assertFalse(allocate_stat_points(other, "atk", 2, "s7-direct").replayed)

    def test_rollback_when_event_creation_fails(self):
        with patch.object(StatAllocationEvent, "save", side_effect=OperationalError("test failure")):
            self.reject(AllocationDatabaseError)

    def test_rollback_when_stats_update_fails(self):
        with patch.object(CharacterStats, "save", side_effect=OperationalError("test failure")):
            self.reject(AllocationDatabaseError)

    def test_database_cause_preserved_and_programming_errors_not_hidden(self):
        with patch.object(CharacterStats, "save", side_effect=OperationalError("test cause")):
            with self.assertRaises(AllocationDatabaseError) as raised:
                allocate_stat_points(self.profile, "atk", 1, "s7-db")
        self.assertIsInstance(raised.exception.__cause__, OperationalError)
        with patch("apps.ecomotor.stat_allocation._eligible", side_effect=RuntimeError("test bug")):
            self.reject(RuntimeError)

    def test_only_stats_and_allocation_history_change_and_s4_reflects_them(self):
        before = self.snapshot()
        allocate_stat_points(self.profile, "atk", 3, "s7-isolated")
        after = self.snapshot()
        for index in range(len(before)):
            if index not in (3, 10):
                self.assertEqual(before[index], after[index])
        overview = get_progress_overview(self.profile)
        self.assertEqual((overview.atk, overview.available_points), (5, 11))
        self.assertEqual(len(list_progress_history(self.profile).entries), 1)

    def test_admin_active_superuser_read_only_and_direct_posts_blocked(self):
        result = allocate_stat_points(self.profile, "atk", 1, "s7-admin")
        model_admin = admin.site._registry[StatAllocationEvent]
        self.assertIsInstance(model_admin, ReadOnlySuperuserAdmin)
        user = get_user_model().objects.create_superuser(username="s7-admin", password="test-only")
        self.client.force_login(user)
        base = "admin:ecomotor_statallocationevent_"
        change = reverse(base + "change", args=[result.allocation_event_id])
        self.assertEqual(self.client.get(change).status_code, 200)
        self.assertEqual(self.client.get(reverse(base + "changelist"), {"q": "s7-admin"}).status_code, 200)
        before = self.snapshot()
        for url in (change, reverse(base + "add"), reverse(base + "delete", args=[result.allocation_event_id])):
            self.assertEqual(self.client.post(url, {"points_spent": 99}).status_code, 403)
        self.assertEqual(self.client.post(reverse(base + "changelist"), {
            "action": "delete_selected", "_selected_action": result.allocation_event_id,
        }).status_code, 200)
        self.assertEqual(before, self.snapshot())
        for updates in ({"is_superuser": False}, {"is_active": False}):
            get_user_model().objects.filter(pk=user.pk).update(**updates)
            self.assertNotEqual(self.client.get(change).status_code, 200)

    def test_admin_anonymous_normal_and_staff_with_permissions_denied(self):
        from django.contrib.auth.models import Permission
        self.client.logout()
        listing = reverse("admin:ecomotor_statallocationevent_changelist")
        self.assertEqual(self.client.get(listing).status_code, 302)
        for staff in (False, True):
            user = get_user_model().objects.create_user(username=f"s7-staff-{staff}", is_staff=staff)
            user.user_permissions.set(Permission.objects.filter(content_type__model="statallocationevent"))
            self.client.force_login(user)
            self.assertNotEqual(self.client.get(listing).status_code, 200)
