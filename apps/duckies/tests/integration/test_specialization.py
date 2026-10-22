from apps.duckies.integration_services import (
    select_initial_specialization_and_outfit,
    switch_specialization_and_outfit,
)
from apps.duckies.services import select_outfit
from apps.ecomotor.models import UserSpecializationProgress

from .fixtures import IntegrationFixture, STAGE_CODES


class SpecializationIntegrationTests(IntegrationFixture):
    def test_first_selection_auto_equips_specialization_outfit(self):
        self.advance_to_final_stage()
        result = select_initial_specialization_and_outfit(self.user, "DEVELOPER")
        self.profile.refresh_from_db()
        self.ducky.refresh_from_db()
        self.assertTrue(result.created)
        self.assertEqual(self.profile.active_specialization_code, "DEVELOPER")
        self.assertEqual(self.ducky.selected_outfit_id, self.spec_outfits["DEVELOPER"].pk)

    def test_first_selection_replay_is_idempotent(self):
        self.advance_to_final_stage()
        first = select_initial_specialization_and_outfit(self.user, "DEVELOPER")
        again = select_initial_specialization_and_outfit(self.user, "DEVELOPER")
        self.assertEqual(first.progress_id, again.progress_id)
        self.assertFalse(again.created)
        self.assertEqual(UserSpecializationProgress.objects.filter(profile=self.profile).count(), 1)

    def test_cannot_choose_other_specialization_outfit(self):
        self.advance_to_final_stage()
        select_initial_specialization_and_outfit(self.user, "DEVELOPER")
        with self.assertRaises(ValueError):
            select_outfit(self.user, self.spec_outfits["GAMER"])

    def test_switch_updates_outfit_and_preserves_per_spec_progress(self):
        self.advance_to_final_stage()
        select_initial_specialization_and_outfit(self.user, "DEVELOPER")
        original = UserSpecializationProgress.objects.get(
            profile=self.profile, specialization=self.specializations["DEVELOPER"],
        )
        original.domain_xp_total = 17
        original.save(update_fields=["domain_xp_total"])
        switch_specialization_and_outfit(self.user, "GAMER", "DEVELOPER")
        self.profile.refresh_from_db()
        self.ducky.refresh_from_db()
        self.assertEqual(self.profile.active_specialization_code, "GAMER")
        self.assertEqual(self.ducky.selected_outfit_id, self.spec_outfits["GAMER"].pk)
        switch_specialization_and_outfit(self.user, "DEVELOPER", "GAMER")
        self.profile.refresh_from_db()
        self.ducky.refresh_from_db()
        original.refresh_from_db()
        self.assertEqual(original.domain_xp_total, 17)
        self.assertEqual(self.ducky.selected_outfit_id, self.spec_outfits["DEVELOPER"].pk)

    def test_switch_preserves_selected_historical_outfit(self):
        self.advance_to_final_stage()
        select_initial_specialization_and_outfit(self.user, "DEVELOPER")
        old = self.historical[STAGE_CODES[2]]
        select_outfit(self.user, old)
        switch_specialization_and_outfit(self.user, "GAMER", "DEVELOPER")
        self.ducky.refresh_from_db()
        self.assertEqual(self.ducky.selected_outfit_id, old.pk)

    def test_stale_switch_does_not_change_active_specialization(self):
        self.advance_to_final_stage()
        select_initial_specialization_and_outfit(self.user, "DEVELOPER")
        with self.assertRaises(ValueError):
            switch_specialization_and_outfit(self.user, "GAMER", "CIBER")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.active_specialization_code, "DEVELOPER")
