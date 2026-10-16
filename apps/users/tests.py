from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import UserProfileBank, UserProfileEcomotor


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='student')

    def test_create_ecomotor_profile(self):
        profile = UserProfileEcomotor.objects.create(
            user=self.user, current_level=1, current_stage_code="test-stage"
        )

        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.historical_xp_total, 0)
        self.assertIsNone(profile.active_specialization_code)

    def test_create_bank_profile(self):
        profile = UserProfileBank.objects.create(user=self.user)

        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)

    def test_ecomotor_profile_is_unique_per_user(self):
        fields = dict(user=self.user, current_level=1, current_stage_code="test-stage")
        UserProfileEcomotor.objects.create(**fields)

        with self.assertRaises(IntegrityError), transaction.atomic():
            UserProfileEcomotor.objects.create(**fields)

        self.assertEqual(UserProfileEcomotor.objects.filter(user=self.user).count(), 1)

    def test_bank_profile_is_unique_per_user(self):
        UserProfileBank.objects.create(user=self.user)

        with self.assertRaises(IntegrityError), transaction.atomic():
            UserProfileBank.objects.create(user=self.user)

        self.assertEqual(UserProfileBank.objects.filter(user=self.user).count(), 1)

    def test_invalid_progress_is_rejected_by_database(self):
        for field, value in [
            ("current_level", 0),
            ("historical_xp_total", -1),
            ("current_stage_code", ""),
            ("current_level", None),
            ("current_stage_code", None),
        ]:
            fields = dict(user=self.user, current_level=1, current_stage_code="test-stage")
            fields[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    UserProfileEcomotor.objects.create(**fields)

    def test_user_does_not_automatically_create_profiles(self):
        self.assertFalse(UserProfileEcomotor.objects.filter(user=self.user).exists())
        self.assertFalse(UserProfileBank.objects.filter(user=self.user).exists())
