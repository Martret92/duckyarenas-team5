"""Admin HTTP policy tests. All catalogs and progress are fictitious test data."""

from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.users.models import UserProfileBank, UserProfileEcomotor

from .models import (
    CharacterStats,
    EvolutionEvent,
    EvolutionStage,
    LevelThreshold,
    Specialization,
    UserSpecializationProgress,
    XPEvent,
)


def admin_url(model, action, obj=None):
    opts = model._meta
    return reverse(
        f"admin:{opts.app_label}_{opts.model_name}_{action}",
        args=[obj.pk] if obj is not None else None,
    )


def create_admin_test_users():
    user_model = get_user_model()
    users = {
        "superuser": user_model.objects.create_superuser(username="admin-test-root"),
        "normal": user_model.objects.create_user(username="admin-test-normal"),
        "staff": user_model.objects.create_user(username="admin-test-staff", is_staff=True),
    }
    users["staff"].user_permissions.set(
        Permission.objects.filter(content_type__app_label__in=["ecomotor", "users"])
    )
    return users


def create_progress_test_data():
    user = get_user_model().objects.create_user(username="admin-test-player")
    profile = UserProfileEcomotor.objects.create(
        user=user, historical_xp_total=23, current_level=2,
        current_stage_code="test-stage", active_specialization_code="test-spec",
    )
    stage = EvolutionStage.objects.create(
        code="test-stage", name="Test stage", ordinal=2, minimum_xp=17,
    )
    specialization = Specialization.objects.create(code="test-spec", name="Test spec")
    stats = CharacterStats.objects.create(
        profile=profile, atk=2, def_stat=3, log_stat=4, spe=6, vel=7,
        int_stat=8, available_points=9,
    )
    xp = XPEvent.objects.create(
        profile=profile, amount=23, xp_before=0, xp_after=23,
        operation_key="test-session-key",
    )
    evolution = EvolutionEvent.objects.create(profile=profile, stage=stage, xp_event=xp)
    progress = UserSpecializationProgress.objects.create(
        profile=profile, specialization=specialization, domain_xp_total=11,
    )
    return {
        UserProfileEcomotor: profile, CharacterStats: stats, XPEvent: xp,
        EvolutionEvent: evolution, UserSpecializationProgress: progress,
    }


class AdminHTTPAssertions:
    """Shared assertions only; tests remain in the two authorized test modules."""

    def snapshot(self, models):
        return {model: list(model.objects.order_by("pk").values()) for model in models}

    def assert_readonly_details(self, objects):
        self.client.force_login(self.users["superuser"])
        for model, obj in objects.items():
            with self.subTest(model=model.__name__):
                listing = self.client.get(admin_url(model, "changelist"))
                self.assertEqual(listing.status_code, 200)
                self.assertIn(obj, listing.context["cl"].result_list)
                self.assertIsNone(listing.context["action_form"])
                detail = self.client.get(admin_url(model, "change", obj))
                self.assertEqual(detail.status_code, 200)
                self.assertFalse(detail.context["adminform"].form.fields)
                for permission in ["has_add_permission", "has_change_permission", "has_delete_permission"]:
                    self.assertFalse(detail.context[permission])
                self.assertNotContains(detail, 'name="_save"')
                self.assertNotContains(detail, 'name="_saveasnew"')
                self.assertNotContains(detail, 'name="_continue"')

    def assert_non_superusers_denied(self, objects):
        before = self.snapshot(objects)
        for role in ["anonymous", "normal", "staff"]:
            self.client.logout()
            if role != "anonymous":
                self.client.force_login(self.users[role])
            expected = 403 if role == "staff" else 302
            for model, obj in objects.items():
                for action, target in [("changelist", None), ("change", obj), ("add", None), ("delete", obj)]:
                    url = admin_url(model, action, target)
                    for method in ["get", "post"]:
                        with self.subTest(role=role, model=model.__name__, action=action, method=method):
                            response = getattr(self.client, method)(url)
                            self.assertEqual(response.status_code, expected)
                            if expected == 302:
                                self.assertTrue(response.url.startswith(reverse("admin:login")))
        self.assertEqual(self.snapshot(objects), before)

    def assert_progress_writes_denied(self, objects):
        self.client.force_login(self.users["superuser"])
        before = self.snapshot(objects)
        # POSTs deliberately include new values and save-as-new to bypass UI controls.
        payload = {
            "historical_xp_total": 999, "current_level": 9, "current_stage_code": "tampered",
            "active_specialization_code": "tampered", "amount": 999, "xp_before": 0,
            "xp_after": 999, "operation_key": "tampered", "domain_xp_total": 999,
            "atk": 999, "available_points": 999, "_save": "Save", "_saveasnew": "Save as new",
        }
        for model, obj in objects.items():
            for action, target in [("add", None), ("change", obj), ("delete", obj)]:
                with self.subTest(model=model.__name__, action=action):
                    url = admin_url(model, action, target)
                    if action != "change":
                        self.assertEqual(self.client.get(url).status_code, 403)
                    response = self.client.post(url, payload | {"post": "yes"})
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(self.snapshot(objects), before)
            response = self.client.post(
                admin_url(model, "changelist"),
                {"action": "delete_selected", "_selected_action": obj.pk, "index": "0", "post": "yes"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(response.context["action_form"])
            self.assertEqual(self.snapshot(objects), before)


class CatalogAdminTests(AdminHTTPAssertions, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = create_admin_test_users()
        cls.objects = {
            LevelThreshold: LevelThreshold.objects.create(level=3, minimum_xp=17, stat_points_awarded=0),
            EvolutionStage: EvolutionStage.objects.create(code="test-third", name="Test third", ordinal=3, minimum_xp=17),
            Specialization: Specialization.objects.create(code="test-spec", name="Test spec"),
        }
        cls.new_values = {
            LevelThreshold: dict(level=4, minimum_xp=29, stat_points_awarded=2),
            EvolutionStage: dict(code="test-fourth", name="Test fourth", ordinal=4, minimum_xp=29),
            Specialization: dict(code="test-other", name="Test other"),
        }

    def setUp(self):
        self.client.force_login(self.users["superuser"])

    def create_profile(self):
        return UserProfileEcomotor.objects.create(
            user=self.users["normal"], current_level=1, current_stage_code="test-stage",
        )

    def test_superuser_can_view_catalog_lists_and_details(self):
        for model, obj in self.objects.items():
            with self.subTest(model=model.__name__):
                listing = self.client.get(admin_url(model, "changelist"))
                self.assertEqual(listing.status_code, 200)
                self.assertIn(obj, listing.context["cl"].result_list)
                self.assertEqual(self.client.get(admin_url(model, "change", obj)).status_code, 200)

    def test_non_superusers_cannot_access_catalogs_even_with_model_permissions(self):
        self.assert_non_superusers_denied(self.objects)

    def test_can_add_valid_rows_to_incomplete_catalogs(self):
        for model, fields in self.new_values.items():
            with self.subTest(model=model.__name__):
                self.assertEqual(self.client.get(admin_url(model, "add")).status_code, 200)
                response = self.client.post(admin_url(model, "add"), fields | {"_save": "Save"})
                self.assertEqual(response.status_code, 302)
                self.assertTrue(model.objects.filter(**fields).exists())
        # Neither levels nor stages form a complete functional catalog.
        self.assertEqual(list(LevelThreshold.objects.values_list("level", flat=True)), [3, 4])
        self.assertEqual(EvolutionStage.objects.count(), 2)

    def test_can_change_valid_rows_without_profiles(self):
        for model, obj in self.objects.items():
            fields = self.new_values[model]
            with self.subTest(model=model.__name__):
                response = self.client.post(admin_url(model, "change", obj), fields | {"_save": "Save"})
                self.assertEqual(response.status_code, 302)
                obj.refresh_from_db()
                for field, value in fields.items():
                    self.assertEqual(getattr(obj, field), value)

    def test_bank_profiles_do_not_lock_catalogs(self):
        UserProfileBank.objects.create(user=self.users["normal"])
        for model, fields in self.new_values.items():
            with self.subTest(model=model.__name__):
                self.assertEqual(self.client.post(admin_url(model, "add"), fields).status_code, 302)

    def test_existing_profile_locks_catalog_add_and_change_posts(self):
        self.create_profile()
        before = self.snapshot(self.objects)
        for model, obj in self.objects.items():
            with self.subTest(model=model.__name__):
                self.assertEqual(self.client.get(admin_url(model, "add")).status_code, 403)
                self.assertEqual(self.client.get(admin_url(model, "changelist")).status_code, 200)
                detail = self.client.get(admin_url(model, "change", obj))
                self.assertEqual(detail.status_code, 200)
                self.assertFalse(detail.context["has_change_permission"])
                self.assertNotContains(detail, 'name="_save"')
                self.assertEqual(self.client.post(admin_url(model, "add"), self.new_values[model]).status_code, 403)
                self.assertEqual(self.client.post(admin_url(model, "change", obj), self.new_values[model]).status_code, 403)
                self.assertEqual(self.snapshot(self.objects), before)

    def test_save_guard_rechecks_profile_existence_at_write_time(self):
        # Simulate a profile appearing after view permissions were checked.
        for model, obj in self.objects.items():
            for action, target in [("add", None), ("change", obj)]:
                with self.subTest(model=model.__name__, action=action):
                    before = self.snapshot(self.objects)
                    model_admin = admin.site._registry[model]
                    original_save = model_admin.save_model

                    def create_profile_then_save(request, instance, form, change):
                        self.create_profile()
                        return original_save(request, instance, form, change)

                    with patch.object(model_admin, "save_model", side_effect=create_profile_then_save):
                        response = self.client.post(admin_url(model, action, target), self.new_values[model])
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(self.snapshot(self.objects), before)
                    self.assertFalse(UserProfileEcomotor.objects.exists())

    def test_catalog_deletion_and_bulk_actions_are_always_denied(self):
        for with_profile in [False, True]:
            if with_profile:
                self.create_profile()
            before = self.snapshot(self.objects)
            for model, obj in self.objects.items():
                with self.subTest(model=model.__name__, with_profile=with_profile):
                    url = admin_url(model, "delete", obj)
                    self.assertEqual(self.client.get(url).status_code, 403)
                    self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)
                    response = self.client.post(
                        admin_url(model, "changelist"),
                        {"action": "delete_selected", "_selected_action": obj.pk, "index": "0", "post": "yes"},
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertIsNone(response.context["action_form"])
                    self.assertEqual(self.snapshot(self.objects), before)

    def test_invalid_individual_values_are_rejected(self):
        invalid_rows = [
            (LevelThreshold, dict(level=0, minimum_xp=0, stat_points_awarded=0)),
            (LevelThreshold, dict(level=4, minimum_xp=-1, stat_points_awarded=0)),
            (LevelThreshold, dict(level=4, minimum_xp=0, stat_points_awarded=-1)),
            (EvolutionStage, dict(code="test-bad", name="Test bad", ordinal=8, minimum_xp=0)),
            (EvolutionStage, dict(code="test-bad", name="Test bad", ordinal=4, minimum_xp=-1)),
            (EvolutionStage, dict(code="", name="Test bad", ordinal=4, minimum_xp=0)),
            (Specialization, dict(code="test-bad", name="")),
            (Specialization, dict(code="x" * 33, name="Test bad")),
        ]
        before = self.snapshot(self.objects)
        for model, fields in invalid_rows:
            with self.subTest(model=model.__name__, fields=fields):
                response = self.client.post(admin_url(model, "add"), fields)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["adminform"].form.errors)
                self.assertEqual(self.snapshot(self.objects), before)
        obj = self.objects[LevelThreshold]
        response = self.client.post(admin_url(LevelThreshold, "change", obj), invalid_rows[0][1])
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["adminform"].form.errors)
        self.assertEqual(self.snapshot(self.objects), before)

    def test_model_uniqueness_is_validated_by_admin(self):
        before = self.snapshot(self.objects)
        for model, obj in self.objects.items():
            fields = {field.name: getattr(obj, field.name) for field in model._meta.fields if not field.primary_key}
            with self.subTest(model=model.__name__):
                response = self.client.post(admin_url(model, "add"), fields)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["adminform"].form.errors)
        self.assertEqual(self.snapshot(self.objects), before)

    def test_search_filters_and_ordering(self):
        for model, fields in self.new_values.items():
            other = model.objects.create(**fields)
            query = str(fields["level"]) if model is LevelThreshold else fields["code"]
            with self.subTest(model=model.__name__):
                result = self.client.get(admin_url(model, "changelist"), {"q": query})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(list(result.context["cl"].result_list), [other])
        for model, params in [
            (LevelThreshold, {"stat_points_awarded": 2}),
            (EvolutionStage, {"ordinal": 4}),
        ]:
            result = self.client.get(admin_url(model, "changelist"), params)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.context["cl"].result_list.count(), 1)
        result = self.client.get(admin_url(LevelThreshold, "changelist"))
        self.assertEqual([obj.level for obj in result.context["cl"].result_list], [3, 4])


class EcomotorProgressAdminTests(AdminHTTPAssertions, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = create_admin_test_users()
        cls.objects = create_progress_test_data()
        del cls.objects[UserProfileEcomotor]

    def test_superuser_can_only_read_progress_and_histories(self):
        self.assert_readonly_details(self.objects)

    def test_non_superusers_cannot_access_progress_even_with_model_permissions(self):
        self.assert_non_superusers_denied(self.objects)

    def test_progress_write_and_bulk_delete_posts_leave_records_unchanged(self):
        self.assert_progress_writes_denied(self.objects)

    def test_progress_search_and_filters(self):
        self.client.force_login(self.users["superuser"])
        for model, obj in self.objects.items():
            with self.subTest(model=model.__name__):
                result = self.client.get(admin_url(model, "changelist"), {"q": "admin-test-player"})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(list(result.context["cl"].result_list), [obj])
                result = self.client.get(admin_url(model, "changelist"), {"q": "missing-player"})
                self.assertEqual(result.context["cl"].result_list.count(), 0)
        for model, params in [
            (CharacterStats, {"profile__current_level": 2}),
            (XPEvent, {"created_at__isnull": "False"}),
            (EvolutionEvent, {"stage__id__exact": self.objects[EvolutionEvent].stage_id}),
            (UserSpecializationProgress, {"specialization__id__exact": self.objects[UserSpecializationProgress].specialization_id}),
        ]:
            result = self.client.get(admin_url(model, "changelist"), params)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.context["cl"].result_list.count(), 1)

    def test_admin_registration_does_not_grant_access_to_other_modules(self):
        self.assertNotIn(UserProfileBank, admin.site._registry)
        self.assertIsInstance(admin.site._registry[get_user_model()], UserAdmin)
        self.client.force_login(self.users["staff"])
        self.assertEqual(self.client.get(admin_url(get_user_model(), "changelist")).status_code, 403)
        index = self.client.get(reverse("admin:index"))
        self.assertEqual(index.status_code, 200)
        self.assertFalse(index.context["app_list"])
