"""Snapshots ficticios; pruebas reales de S7-A, aislamiento y lecturas S9-A."""

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase as IsolatedTestCase
from unittest.mock import patch
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import OperationalError, connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config
from .models import CharacterStats, EvolutionStage, StatAllocationEvent, XPEvent, EvolutionEvent
from .progress_queries import (
    InconsistentQueryStateError, InvalidHistoryParametersError,
    InvalidQueryProfileError, ProgressQueryDatabaseError,
)
from .stat_allocation import allocate_stat_points
from .stat_allocation_queries import list_stat_allocation_history
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


class StatAllocationQueryTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="s9-query-a")
        self.other = create_xp_profile(username="s9-query-b")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)
        grant_historical_xp(self.profile, 102, "s9-reach-actual")

    def allocate(self, key="s9-private-operation", attribute="atk", points=1):
        return allocate_stat_points(self.profile, attribute, points, key)

    def snapshot(self):
        return [list(model.objects.order_by("pk").values()) for model in (
            get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
            XPEvent, EvolutionEvent, StatAllocationEvent, EvolutionStage,
        )]

    def test_empty_history(self):
        page = list_stat_allocation_history(self.profile)
        self.assertEqual(page.entries, ())
        self.assertFalse(page.has_more)
        self.assertIsNone(page.next_before_id)

    def test_real_allocation_snapshots_and_label_without_private_fields(self):
        result = self.allocate(points=3)
        entry = list_stat_allocation_history(self.profile).entries[0]
        self.assertEqual(entry.id, result.allocation_event_id)
        for name in ("attribute", "points_spent", "increase_applied", "attribute_before",
                     "attribute_after", "available_points_before", "available_points_after",
                     "stage_code_at_allocation"):
            self.assertEqual(getattr(entry, name), getattr(result, name))
        self.assertEqual(entry.attribute_label, "ATK")
        self.assertEqual(entry.created_at, StatAllocationEvent.objects.get(pk=entry.id).created_at)
        self.assertNotIn("operation_key", {field.name for field in fields(entry)})
        self.assertNotIn("profile_id", {field.name for field in fields(entry)})

    def test_descending_order_and_pages_without_duplicates(self):
        ids = [self.allocate(str(n)).allocation_event_id for n in range(5)]
        first = list_stat_allocation_history(self.profile, limit=2)
        second = list_stat_allocation_history(self.profile, limit=2, before_id=first.next_before_id)
        third = list_stat_allocation_history(self.profile, limit=2, before_id=second.next_before_id)
        self.assertEqual([e.id for page in (first, second, third) for e in page.entries], ids[::-1])
        self.assertTrue(first.has_more)
        self.assertTrue(second.has_more)
        self.assertFalse(third.has_more)
        self.assertIsNone(third.next_before_id)

    def test_exact_limit_has_no_more(self):
        self.allocate("one")
        self.allocate("two")
        page = list_stat_allocation_history(self.profile, limit=2)
        self.assertEqual(len(page.entries), 2)
        self.assertFalse(page.has_more)
        self.assertIsNone(page.next_before_id)

    def test_default_and_maximum_page_sizes(self):
        StatAllocationEvent.objects.bulk_create([
            StatAllocationEvent(profile=self.profile, operation_key=f"fictitious-page-{n}",
                                attribute="atk", points_spent=1, increase_applied=1,
                                available_points_before=2, available_points_after=1,
                                attribute_before=3, attribute_after=4,
                                stage_code_at_allocation="test-historical-stage")
            for n in range(101)
        ])
        default = list_stat_allocation_history(self.profile)
        maximum = list_stat_allocation_history(self.profile, limit=100)
        self.assertEqual(len(default.entries), 50)
        self.assertEqual(len(maximum.entries), 100)
        self.assertTrue(default.has_more)
        self.assertTrue(maximum.has_more)

    def test_exclusive_cursor_and_cursor_without_matches(self):
        first = self.allocate("first").allocation_event_id
        second = self.allocate("second").allocation_event_id
        page = list_stat_allocation_history(self.profile, before_id=second)
        self.assertEqual([entry.id for entry in page.entries], [first])
        self.assertEqual(list_stat_allocation_history(self.profile, before_id=first).entries, ())

    def test_invalid_limits(self):
        for value in (0, -1, 101, True, False, 1.0, "1", None):
            with self.subTest(value=value), self.assertRaises(InvalidHistoryParametersError):
                list_stat_allocation_history(self.profile, limit=value)

    def test_invalid_cursors(self):
        for value in (0, -1, True, False, 1.0, "1", 2**64):
            with self.subTest(value=value), self.assertRaises(InvalidHistoryParametersError):
                list_stat_allocation_history(self.profile, before_id=value)

    def test_isolation_between_profiles(self):
        self.allocate()
        self.assertEqual(list_stat_allocation_history(self.other).entries, ())
        grant_historical_xp(self.other, 102, "other-actual")
        result = allocate_stat_points(self.other, "vel", 1, "other-secret")
        self.assertNotIn(result.allocation_event_id, [e.id for e in list_stat_allocation_history(self.profile).entries])

    def test_replay_is_one_entry(self):
        first = self.allocate()
        replay = self.allocate()
        self.assertTrue(replay.replayed)
        self.assertEqual([e.id for e in list_stat_allocation_history(self.profile).entries], [first.allocation_event_id])

    def test_old_snapshots_after_allocations_and_s3(self):
        self.allocate("original", points=2)
        original = list_stat_allocation_history(self.profile).entries[0]
        self.allocate("later", points=3)
        grant_historical_xp(self.profile, 10, "later-xp")
        self.assertEqual(list_stat_allocation_history(self.profile).entries[-1], original)

    def test_history_independent_of_configuration_and_current_catalogs(self):
        self.allocate()
        original = list_stat_allocation_history(self.profile)
        stage = EvolutionStage.objects.get(ordinal=7)
        stage.code = "changed-test-code"
        stage.save(update_fields=["code"])
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None):
            self.assertEqual(list_stat_allocation_history(self.profile), original)

    def test_inconsistent_snapshot_is_rejected_without_repair(self):
        result = self.allocate()
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA ignore_check_constraints = ON")
            try:
                cursor.execute("UPDATE ecomotor_statallocationevent SET attribute_after = 900 WHERE id = %s",
                               [result.allocation_event_id])
            finally:
                cursor.execute("PRAGMA ignore_check_constraints = OFF")
        before = self.snapshot()
        with self.assertRaises(InconsistentQueryStateError):
            list_stat_allocation_history(self.profile)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_historical_fields_strictly_rejected(self):
        self.allocate()
        event = StatAllocationEvent.objects.first()
        for name, value in (("attribute", "ATK"), ("points_spent", True), ("attribute_before", 1.5),
                            ("stage_code_at_allocation", ""), ("created_at", "not-a-date"),
                            ("profile_id", self.other.pk), ("available_points_before", 2**64),
                            ("points_spent", 0), ("increase_applied", -1),
                            ("attribute_after", 2**64), ("available_points_after", -1)):
            with self.subTest(field=name):
                changed = StatAllocationEvent.objects.get(pk=event.pk)
                setattr(changed, name, value)
                with patch("apps.ecomotor.stat_allocation_queries.StatAllocationEvent.objects.using") as manager:
                    manager.return_value.filter.return_value.order_by.return_value.__getitem__.return_value = [changed]
                    with self.assertRaises(InconsistentQueryStateError):
                        list_stat_allocation_history(self.profile)

    def test_fractional_legacy_snapshot_in_sqlite_is_not_coerced(self):
        result = self.allocate()
        # SQLite permite REAL en una columna INTEGER; la igualdad sigue cumpliéndose.
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_statallocationevent SET attribute_before = 2.5, "
                           "attribute_after = 3.5 WHERE id = %s", [result.allocation_event_id])
        with self.assertRaises(InconsistentQueryStateError):
            list_stat_allocation_history(self.profile)

    def test_invalid_unpersisted_and_deleted_profiles(self):
        for profile in (None, object(), UserProfileEcomotor(), True):
            with self.subTest(profile=profile), self.assertRaises(InvalidQueryProfileError):
                list_stat_allocation_history(profile)
        stale = UserProfileEcomotor.objects.get(pk=self.other.pk)
        self.other.delete()
        with self.assertRaises(InvalidQueryProfileError):
            list_stat_allocation_history(stale)

    def test_missing_stats_and_invalid_structure(self):
        CharacterStats.objects.filter(profile=self.other).delete()
        with self.assertRaises(InconsistentQueryStateError):
            list_stat_allocation_history(self.other)
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="x" * 33)
        with self.assertRaises(InconsistentQueryStateError):
            list_stat_allocation_history(self.profile)

    def test_stale_instance_is_not_trusted(self):
        self.profile.historical_xp_total = -1
        self.profile.current_stage_code = ""
        self.assertEqual(list_stat_allocation_history(self.profile).entries, ())

    def test_user_identity_representation_does_not_affect_local_history(self):
        result = self.allocate()
        for user_id in (UUID("12345678-1234-5678-1234-567812345678"), "opaque-core-user"):
            with self.subTest(user_id=user_id):
                current = UserProfileEcomotor.objects.get(pk=self.profile.pk)
                # Simula una fila recargada con identidad opaca, sin cambiar el esquema User.
                current.user_id = user_id
                with patch("apps.ecomotor.stat_allocation_queries.UserProfileEcomotor.objects.using") as manager:
                    manager.return_value.filter.return_value.first.return_value = current
                    page = list_stat_allocation_history(self.profile)
                manager.assert_called_once_with(self.profile._state.db)
                manager.return_value.filter.assert_called_once_with(pk=self.profile.pk)
                self.assertEqual([entry.id for entry in page.entries], [result.allocation_event_id])
                self.assertEqual(list_stat_allocation_history(self.other).entries, ())

    def test_database_error_preserves_cause(self):
        error = OperationalError("s9-test-private-error")
        with patch("apps.ecomotor.stat_allocation_queries.StatAllocationEvent.objects.using", side_effect=error), \
                self.assertRaises(ProgressQueryDatabaseError) as caught:
            list_stat_allocation_history(self.profile)
        self.assertIs(caught.exception.__cause__, error)

    def test_programming_errors_are_not_masked(self):
        with patch("apps.ecomotor.stat_allocation_queries.StatAllocationEvent.objects.using", side_effect=RuntimeError), \
                self.assertRaises(RuntimeError):
            list_stat_allocation_history(self.profile)

    def test_results_are_immutable(self):
        self.allocate()
        page = list_stat_allocation_history(self.profile)
        self.assertIsInstance(page.entries, tuple)
        for obj, name, value in ((page, "has_more", True), (page.entries[0], "points_spent", 5)):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, name, value)

    def test_constant_query_count_and_select_only(self):
        self.allocate("one")
        self.allocate("two")
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            list_stat_allocation_history(self.profile)
        self.assertEqual(len(queries), 3)
        self.assertTrue(all(row["sql"].lstrip().upper().startswith("SELECT ") for row in queries))
        self.assertEqual(self.snapshot(), before)


class StatAllocationQueryAliasTests(IsolatedTestCase):
    def test_uses_profile_alias_without_default_queries(self):
        with TemporaryDirectory(prefix="ducky-s9-alias-") as directory:
            alias = "s9_query_test"
            config = connections["default"].settings_dict.copy()
            config["NAME"] = str(Path(directory) / "test.sqlite3")
            config["OPTIONS"] = config["OPTIONS"].copy()
            connections.databases[alias] = config
            database = connections[alias]
            try:
                executor = MigrationExecutor(database)
                executor.migrate(executor.loader.graph.leaf_nodes())
                create_xp_catalogs(alias)
                profile = create_xp_profile(alias)
                with patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION):
                    grant_historical_xp(profile, 102, "s9-alias-xp")
                    result = allocate_stat_points(profile, "atk", 1, "s9-alias-allocation")
                def no_default(*args):
                    raise AssertionError("La consulta usó default.")
                with connections["default"].execute_wrapper(no_default), CaptureQueriesContext(database) as queries:
                    page = list_stat_allocation_history(profile)
                self.assertEqual(page.entries[0].id, result.allocation_event_id)
                self.assertTrue(all(row["sql"].lstrip().upper().startswith("SELECT ") for row in queries))
            finally:
                database.close()
                del connections[alias]
                del connections.databases[alias]
