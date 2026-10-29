
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.ecomotor.models import EvolutionStage, Specialization
from apps.users.models import UserProfileEcomotor

from apps.duckies.models import (
    Ducky,
    EvolutionItem,
    Item,
    SpecializationItem,
)


class DuckiesHTTPBusinessRulesTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="http_business_user",
            password="test_password_123",
        )

        self.stage_1 = EvolutionStage.objects.create(
            code="HTTP_STAGE_1",
            name="Etapa 1",
            ordinal=1,
            minimum_xp=0,
        )

        self.stage_2 = EvolutionStage.objects.create(
            code="HTTP_STAGE_2",
            name="Etapa 2",
            ordinal=2,
            minimum_xp=100,
        )

        self.profile = UserProfileEcomotor.objects.create(
            user=self.user,
            current_level=1,
            current_stage_code=self.stage_1.code,
        )

        self.outfit_1 = Item.objects.create(
            code="http_outfit_stage_1",
            name="Vestimenta etapa 1",
            category=Item.HISTORICAL,
        )

        self.outfit_2 = Item.objects.create(
            code="http_outfit_stage_2",
            name="Vestimenta etapa 2",
            category=Item.HISTORICAL,
        )

        EvolutionItem.objects.create(
            stage=self.stage_1,
            item=self.outfit_1,
        )

        EvolutionItem.objects.create(
            stage=self.stage_2,
            item=self.outfit_2,
        )

        self.specialization_1 = Specialization.objects.create(
            code="HTTP_GAMER",
            name="Gamer HTTP",
        )

        self.specialization_2 = Specialization.objects.create(
            code="HTTP_DEVELOPER",
            name="Developer HTTP",
        )

        self.specialization_outfit_1 = Item.objects.create(
            code="http_gamer_outfit",
            name="Vestimenta Gamer",
            category=Item.SPECIALIZATION,
        )

        self.specialization_outfit_2 = Item.objects.create(
            code="http_developer_outfit",
            name="Vestimenta Developer",
            category=Item.SPECIALIZATION,
        )

        SpecializationItem.objects.create(
            specialization=self.specialization_1,
            item=self.specialization_outfit_1,
        )

        SpecializationItem.objects.create(
            specialization=self.specialization_2,
            item=self.specialization_outfit_2,
        )

        self.ducky = Ducky.objects.create(
            user=self.user,
            sex="male",
            selected_outfit=self.outfit_1,
        )

        self.client.force_login(self.user)

    def select(self, item):
        return self.client.post(
            reverse("duckies:select-outfit"),
            {"item_id": item.pk},
        )

    def activate_specialization(self):
        self.profile.active_specialization_code = (
            self.specialization_1.code
        )
        self.profile.save(
            update_fields=["active_specialization_code"]
        )

    def test_future_historical_outfit_is_blocked(self):
        response = self.select(self.outfit_2)

        self.assertEqual(response.status_code, 409)

        self.ducky.refresh_from_db()
        self.assertEqual(
            self.ducky.selected_outfit_id,
            self.outfit_1.pk,
        )

    def test_current_historical_outfit_is_allowed(self):
        response = self.select(self.outfit_1)

        self.assertEqual(response.status_code, 302)

    def test_previous_historical_outfit_blocked_before_specialization(self):
        self.profile.current_stage_code = self.stage_2.code
        self.profile.save(
            update_fields=["current_stage_code"]
        )

        response = self.select(self.outfit_1)

        self.assertEqual(response.status_code, 409)

    def test_previous_historical_outfit_allowed_after_specialization(self):
        self.profile.current_stage_code = self.stage_2.code
        self.profile.active_specialization_code = (
            self.specialization_1.code
        )
        self.profile.save(
            update_fields=[
                "current_stage_code",
                "active_specialization_code",
            ]
        )

        response = self.select(self.outfit_1)

        self.assertEqual(response.status_code, 302)

        self.ducky.refresh_from_db()
        self.assertEqual(
            self.ducky.selected_outfit_id,
            self.outfit_1.pk,
        )

    def test_specialization_outfit_blocked_without_specialization(self):
        response = self.select(self.specialization_outfit_1)

        self.assertEqual(response.status_code, 409)

    def test_active_specialization_outfit_is_allowed(self):
        self.activate_specialization()

        response = self.select(self.specialization_outfit_1)

        self.assertEqual(response.status_code, 302)

        self.ducky.refresh_from_db()
        self.assertEqual(
            self.ducky.selected_outfit_id,
            self.specialization_outfit_1.pk,
        )

    def test_other_specialization_outfit_is_blocked(self):
        self.activate_specialization()

        response = self.select(self.specialization_outfit_2)

        self.assertEqual(response.status_code, 409)

        self.ducky.refresh_from_db()
        self.assertEqual(
            self.ducky.selected_outfit_id,
            self.outfit_1.pk,
        )

    def test_inactive_historical_outfit_is_blocked(self):
        self.outfit_1.is_active = False
        self.outfit_1.save(update_fields=["is_active"])

        response = self.select(self.outfit_1)

        self.assertEqual(response.status_code, 409)

    def test_non_outfit_item_is_rejected(self):
        item = Item.objects.create(
            code="http_non_outfit",
            name="Objeto de defensa",
            category=Item.DEFENSE,
        )

        response = self.select(item)

        self.assertEqual(response.status_code, 409)

    def test_outfit_catalog_respects_active_specialization(self):
        self.activate_specialization()

        response = self.client.get(
            reverse("duckies:outfits")
        )

        self.assertEqual(response.status_code, 200)

        specializations = response.context["specializations"]

        allowed_codes = {
            entry["specialization"].code
            for entry in specializations
            if entry["allowed"]
        }

        self.assertEqual(
            allowed_codes,
            {self.specialization_1.code},
        )
