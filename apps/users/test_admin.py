"""HTTP checks for the read-only Parte A profile; Bank is not registered."""

from django.test import TestCase

from apps.ecomotor.test_admin import (
    AdminHTTPAssertions,
    admin_url,
    create_admin_test_users,
    create_progress_test_data,
)

from .models import UserProfileEcomotor


class UserProfileEcomotorAdminTests(AdminHTTPAssertions, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = create_admin_test_users()
        cls.objects = create_progress_test_data()

    def test_superuser_can_only_read_ecomotor_profile(self):
        self.assert_readonly_details({UserProfileEcomotor: self.objects[UserProfileEcomotor]})

    def test_non_superusers_cannot_access_profile_even_with_model_permissions(self):
        self.assert_non_superusers_denied({UserProfileEcomotor: self.objects[UserProfileEcomotor]})

    def test_profile_write_and_bulk_delete_posts_preserve_all_progress(self):
        # Snapshot dependent stats and histories too: deletion must not cascade.
        self.assert_progress_writes_denied(self.objects)

    def test_profile_search_and_filters(self):
        self.client.force_login(self.users["superuser"])
        profile = self.objects[UserProfileEcomotor]
        url = admin_url(UserProfileEcomotor, "changelist")
        for params in [
            {"q": "admin-test-player"}, {"current_level": 2},
            {"current_stage_code": "test-stage"}, {"active_specialization_code": "test-spec"},
        ]:
            with self.subTest(params=params):
                response = self.client.get(url, params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(list(response.context["cl"].result_list), [profile])
        response = self.client.get(url, {"q": "missing-player"})
        self.assertEqual(response.context["cl"].result_list.count(), 0)
