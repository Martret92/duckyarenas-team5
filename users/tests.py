from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import UserProfileBank, UserProfileEcomotor


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='student')

    def test_create_ecomotor_profile(self):
        profile = UserProfileEcomotor.objects.create(user=self.user)

        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)

    def test_create_bank_profile(self):
        profile = UserProfileBank.objects.create(user=self.user)

        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)

    def test_ecomotor_profile_is_unique_per_user(self):
        UserProfileEcomotor.objects.create(user=self.user)

        with self.assertRaises(IntegrityError), transaction.atomic():
            UserProfileEcomotor.objects.create(user=self.user)

        self.assertEqual(UserProfileEcomotor.objects.filter(user=self.user).count(), 1)

    def test_bank_profile_is_unique_per_user(self):
        UserProfileBank.objects.create(user=self.user)

        with self.assertRaises(IntegrityError), transaction.atomic():
            UserProfileBank.objects.create(user=self.user)

        self.assertEqual(UserProfileBank.objects.filter(user=self.user).count(), 1)
