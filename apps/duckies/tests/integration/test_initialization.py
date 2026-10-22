from apps.duckies.models import Ducky
from apps.duckies.integration_services import initialize_player_ducky
from apps.ecomotor.models import CharacterStats
from apps.users.models import UserProfileEcomotor
from apps.bank.models import Wallet

from .fixtures import IntegrationFixture, STAGE_CODES


class PlayerInitializationTests(IntegrationFixture):
    def test_player_has_one_profile_stats_ducky_and_wallet(self):
        self.assertEqual(UserProfileEcomotor.objects.filter(user=self.user).count(), 1)
        self.assertEqual(CharacterStats.objects.filter(profile=self.profile).count(), 1)
        self.assertEqual(Ducky.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Wallet.objects.filter(user=self.user).count(), 1)
        self.assertEqual(self.ducky.selected_outfit_id, self.historical[STAGE_CODES[0]].pk)

    def test_repeating_initialization_does_not_duplicate(self):
        repeated = initialize_player_ducky(self.user, "male")
        self.assertEqual(repeated.pk, self.ducky.pk)
        self.assertEqual(UserProfileEcomotor.objects.filter(user=self.user).count(), 1)
        self.assertEqual(CharacterStats.objects.filter(profile=self.profile).count(), 1)
        self.assertEqual(Ducky.objects.filter(user=self.user).count(), 1)

    def test_incompatible_sex_rejected_without_changes(self):
        with self.assertRaises(ValueError):
            initialize_player_ducky(self.user, "female")
        self.ducky.refresh_from_db()
        self.assertEqual(self.ducky.sex, "male")
