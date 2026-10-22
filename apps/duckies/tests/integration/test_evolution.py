from apps.duckies.integration_services import grant_xp_and_sync_outfit
from apps.duckies.services import select_outfit
from apps.ecomotor.models import XPEvent, EvolutionEvent

from .fixtures import IntegrationFixture, STAGE_CODES


class HistoricalProgressionTests(IntegrationFixture):
    def test_xp_progresses_stage_and_outfit(self):
        grant_xp_and_sync_outfit(self.user, 200, "xp-to-roman")
        self.profile.refresh_from_db()
        self.ducky.refresh_from_db()
        self.assertEqual(self.profile.current_stage_code, STAGE_CODES[2])
        self.assertEqual(self.ducky.selected_outfit_id, self.historical[STAGE_CODES[2]].pk)
        self.assertEqual(self.profile.historical_xp_total, 200)

    def test_replayed_xp_does_not_duplicate_events(self):
        first = grant_xp_and_sync_outfit(self.user, 200, "xp-once")
        second = grant_xp_and_sync_outfit(self.user, 200, "xp-once")
        self.profile.refresh_from_db()
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(self.profile.historical_xp_total, 200)
        self.assertEqual(XPEvent.objects.filter(profile=self.profile).count(), 1)
        self.assertEqual(EvolutionEvent.objects.filter(profile=self.profile).count(), 2)

    def test_future_historical_outfit_is_locked(self):
        with self.assertRaises(ValueError):
            select_outfit(self.user, self.historical[STAGE_CODES[3]])

    def test_before_specialization_old_outfit_is_not_selectable(self):
        grant_xp_and_sync_outfit(self.user, 200, "xp-to-roman")
        with self.assertRaises(ValueError):
            select_outfit(self.user, self.historical[STAGE_CODES[0]])

    def test_xp_does_not_credit_bank_automatically(self):
        grant_xp_and_sync_outfit(self.user, 100, "xp-no-coins")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 0)
