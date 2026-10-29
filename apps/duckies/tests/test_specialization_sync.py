
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ecomotor.models import EvolutionStage, Specialization
from apps.users.models import UserProfileEcomotor

from apps.duckies.models import (
    Ducky,
    EvolutionItem,
    Item,
    SpecializationItem,
)

from apps.duckies.services import (
    sync_specialization_outfit,
    validate_selected_outfit,
)


class DuckiesSpecializationSyncTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="specialization_sync_user"
        )

        self.stage = EvolutionStage.objects.create(
            code="SYNC_STAGE_1",
            name="Etapa inicial",
            ordinal=1,
            minimum_xp=0,
        )

        self.profile = UserProfileEcomotor.objects.create(
            user=self.user,
            current_level=1,
            current_stage_code=self.stage.code,
        )

        self.historical = Item.objects.create(
            code="sync_historical",
            name="Vestimenta histórica",
            category=Item.HISTORICAL,
        )

        EvolutionItem.objects.create(
            stage=self.stage,
            item=self.historical,
        )

        self.gamer = Specialization.objects.create(
            code="SYNC_GAMER",
            name="Gamer",
        )

        self.developer = Specialization.objects.create(
            code="SYNC_DEVELOPER",
            name="Developer",
        )

        self.gamer_outfit = Item.objects.create(
            code="sync_gamer_outfit",
            name="Vestimenta Gamer",
            category=Item.SPECIALIZATION,
        )

        self.developer_outfit = Item.objects.create(
            code="sync_developer_outfit",
            name="Vestimenta Developer",
            category=Item.SPECIALIZATION,
        )

        SpecializationItem.objects.create(
            specialization=self.gamer,
            item=self.gamer_outfit,
        )

        SpecializationItem.objects.create(
            specialization=self.developer,
            item=self.developer_outfit,
        )

        self.ducky = Ducky.objects.create(
            user=self.user,
            sex="male",
            selected_outfit=self.historical,
        )

    def activate(self, specialization):
        self.profile.active_specialization_code = specialization.code
        self.profile.save(
            update_fields=["active_specialization_code"]
        )

    def selected_outfit_id(self):
        self.ducky.refresh_from_db()
        return self.ducky.selected_outfit_id

    def test_first_specialization_equips_outfit(self):
        self.activate(self.gamer)

        sync_specialization_outfit(
            self.user,
            None,
            self.gamer.code,
            first_selection=True,
        )

        self.assertEqual(
            self.selected_outfit_id(),
            self.gamer_outfit.pk,
        )

    def test_change_from_gamer_to_developer(self):
        self.ducky.selected_outfit = self.gamer_outfit
        self.ducky.save(update_fields=["selected_outfit"])

        self.activate(self.developer)

        sync_specialization_outfit(
            self.user,
            self.gamer.code,
            self.developer.code,
        )

        self.assertEqual(
            self.selected_outfit_id(),
            self.developer_outfit.pk,
        )

    def test_change_preserves_historical_outfit(self):
        self.activate(self.developer)

        sync_specialization_outfit(
            self.user,
            self.gamer.code,
            self.developer.code,
        )

        self.assertEqual(
            self.selected_outfit_id(),
            self.historical.pk,
        )

    def test_replay_preserves_manual_historical_outfit(self):
        self.activate(self.gamer)

        sync_specialization_outfit(
            self.user,
            self.gamer.code,
            self.gamer.code,
        )

        self.assertEqual(
            self.selected_outfit_id(),
            self.historical.pk,
        )

    def test_rejects_specialization_mismatch(self):
        self.activate(self.gamer)

        with self.assertRaises(ValueError):
            sync_specialization_outfit(
                self.user,
                None,
                self.developer.code,
                first_selection=True,
            )

        self.assertEqual(
            self.selected_outfit_id(),
            self.historical.pk,
        )

    def test_rejects_missing_previous_specialization(self):
        self.activate(self.developer)

        with self.assertRaises(ValueError):
            sync_specialization_outfit(
                self.user,
                None,
                self.developer.code,
            )

        self.assertEqual(
            self.selected_outfit_id(),
            self.historical.pk,
        )

    def test_rejects_invalid_first_selection(self):
        self.activate(self.gamer)

        with self.assertRaises(ValueError):
            sync_specialization_outfit(
                self.user,
                self.developer.code,
                self.gamer.code,
                first_selection=True,
            )

        self.assertEqual(
            self.selected_outfit_id(),
            self.historical.pk,
        )

    def test_validates_active_specialization_outfit(self):
        self.activate(self.gamer)

        sync_specialization_outfit(
            self.user,
            None,
            self.gamer.code,
            first_selection=True,
        )

        result = validate_selected_outfit(self.user)

        self.assertEqual(
            result.selected_outfit_id,
            self.gamer_outfit.pk,
        )

    def test_rejects_inactive_specialization_outfit(self):
        self.activate(self.gamer)

        self.gamer_outfit.is_active = False
        self.gamer_outfit.save(update_fields=["is_active"])

        with self.assertRaises(ValueError):
            sync_specialization_outfit(
                self.user,
                None,
                self.gamer.code,
                first_selection=True,
            )

        self.assertEqual(
            self.selected_outfit_id(),
            self.historical.pk,
        )
