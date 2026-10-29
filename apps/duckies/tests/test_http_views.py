
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse

from apps.duckies.forms import EquipItemForm, OutfitSelectionForm
from django.template.loader import get_template

from apps.ecomotor.models import EvolutionStage
from apps.users.models import UserProfileEcomotor

from apps.duckies.models import (
    Ducky,
    EquipmentSlot,
    EvolutionItem,
    EquippedItem,
    InventoryItem,
    Item,
)

from apps.duckies.services import initialize_ducky, grant_item


class DuckiesURLTests(SimpleTestCase):

    def test_namespaced_routes(self):
        names = (
            "detail",
            "inventory",
            "outfits",
            "museum",
            "select-outfit",
            "equip",
        )

        for name in names:
            with self.subTest(route=name):
                url = reverse(f"duckies:{name}")
                self.assertTrue(resolve(url).func)


class DuckiesFormTests(SimpleTestCase):

    def test_valid_outfit_id(self):
        form = OutfitSelectionForm({"item_id": 5})
        self.assertTrue(form.is_valid())

    def test_invalid_outfit_id(self):
        for value in ("", "abc", "0", "-1"):
            with self.subTest(value=value):
                form = OutfitSelectionForm({"item_id": value})
                self.assertFalse(form.is_valid())

    def test_valid_inventory_id(self):
        form = EquipItemForm({"inventory_id": 3})
        self.assertTrue(form.is_valid())

    def test_invalid_inventory_id(self):
        for value in ("", "abc", "0", "-1"):
            with self.subTest(value=value):
                form = EquipItemForm({"inventory_id": value})
                self.assertFalse(form.is_valid())


class DuckiesAuthenticationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="duckies_http_test",
            password="test_password_123",
        )

    def test_anonymous_users_are_redirected(self):
        names = (
            "detail",
            "inventory",
            "outfits",
            "museum",
            "select-outfit",
            "equip",
        )

        for name in names:
            with self.subTest(route=name):
                response = self.client.get(
                    reverse(f"duckies:{name}")
                )
                self.assertEqual(response.status_code, 302)

    def test_get_views_reject_post(self):
        self.client.force_login(self.user)

        names = (
            "detail",
            "inventory",
            "outfits",
            "museum",
        )

        for name in names:
            with self.subTest(route=name):
                response = self.client.post(
                    reverse(f"duckies:{name}")
                )
                self.assertEqual(response.status_code, 405)

    def test_post_views_reject_get(self):
        self.client.force_login(self.user)

        names = ("select-outfit", "equip")

        for name in names:
            with self.subTest(route=name):
                response = self.client.get(
                    reverse(f"duckies:{name}")
                )
                self.assertEqual(response.status_code, 405)

    def test_missing_ducky_returns_404(self):
        self.client.force_login(self.user)

        names = (
            "detail",
            "inventory",
            "outfits",
            "museum",
        )

        for name in names:
            with self.subTest(route=name):
                response = self.client.get(
                    reverse(f"duckies:{name}")
                )
                self.assertEqual(response.status_code, 404)

    @patch("apps.duckies.views.get_ducky")
    def test_detail_renders_with_mocked_ducky(self, mock_get_ducky):
        from unittest.mock import Mock

        self.client.force_login(self.user)

        mock_ducky = Mock()
        mock_ducky.pk = 1
        mock_ducky.sex = "male"
        mock_ducky.selected_outfit = None
        mock_get_ducky.return_value = mock_ducky

        with patch(
            "apps.duckies.views.get_equipment",
            return_value=[],
        ):
            response = self.client.get(
                reverse("duckies:detail")
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "duckies/detail.html",
        )
        self.assertEqual(
            response.context["ducky"],
            mock_ducky,
        )


class DuckiesTemplateTests(SimpleTestCase):

    def test_all_templates_compile(self):
        templates = (
            "base",
            "detail",
            "inventory",
            "outfits",
            "museum",
        )

        for name in templates:
            with self.subTest(template=name):
                get_template(f"duckies/{name}.html")



class DuckiesRealHTTPTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="http_real_user",
            password="test_password_123",
        )

        self.other_user = User.objects.create_user(
            username="http_other_user",
            password="test_password_123",
        )

        self.stage = EvolutionStage.objects.create(
            code="HTTP_TEST_STAGE",
            name="Etapa de prueba",
            ordinal=1,
            minimum_xp=0,
        )

        for user in (self.user, self.other_user):
            UserProfileEcomotor.objects.create(
                user=user,
                current_level=1,
                current_stage_code=self.stage.code,
            )

        self.outfit = Item.objects.create(
            code="http_historical_outfit",
            name="Vestimenta histórica HTTP",
            category=Item.HISTORICAL,
        )

        EvolutionItem.objects.create(
            stage=self.stage,
            item=self.outfit,
        )

        self.ducky = initialize_ducky(self.user, "male")
        self.other_ducky = initialize_ducky(
            self.other_user, "female"
        )

        self.slot = EquipmentSlot.objects.create(
            code="HTTP_DEFENSE_SLOT",
            name="Defensa HTTP",
        )

        self.item = Item.objects.create(
            code="http_defense_item",
            name="Escudo HTTP",
            category=Item.DEFENSE,
            slot=self.slot,
        )

        grant_item(
            self.user,
            self.item,
            1,
            "http_grant_1",
        )

        self.inventory_item = InventoryItem.objects.get(
            ducky=self.ducky,
            item=self.item,
        )

        self.client.force_login(self.user)

    def test_inventory_page_renders(self):
        response = self.client.get(
            reverse("duckies:inventory")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "duckies/inventory.html",
        )

        self.assertContains(response, self.item.name)

    def test_outfits_page_renders(self):
        response = self.client.get(
            reverse("duckies:outfits")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "duckies/outfits.html",
        )

        self.assertContains(response, self.outfit.name)

    def test_museum_page_renders(self):
        response = self.client.get(
            reverse("duckies:museum")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "duckies/museum.html",
        )

        self.assertContains(response, self.stage.name)

    def test_inventory_invalid_form_returns_400(self):
        response = self.client.post(
            reverse("duckies:equip"),
            {"inventory_id": -1},
        )

        self.assertEqual(response.status_code, 400)

    def test_outfit_invalid_form_returns_400(self):
        response = self.client.post(
            reverse("duckies:select-outfit"),
            {"item_id": "invalid"},
        )

        self.assertEqual(response.status_code, 400)

    def test_nonexistent_inventory_returns_404(self):
        response = self.client.post(
            reverse("duckies:equip"),
            {"inventory_id": 999999},
        )

        self.assertEqual(response.status_code, 404)

    def test_nonexistent_outfit_returns_404(self):
        response = self.client.post(
            reverse("duckies:select-outfit"),
            {"item_id": 999999},
        )

        self.assertEqual(response.status_code, 404)

    def test_cannot_equip_other_users_item(self):
        grant_item(
            self.other_user,
            self.item,
            1,
            "http_other_grant",
        )

        other_inventory = InventoryItem.objects.get(
            ducky=self.other_ducky,
            item=self.item,
        )

        response = self.client.post(
            reverse("duckies:equip"),
            {"inventory_id": other_inventory.pk},
        )

        self.assertEqual(response.status_code, 404)

        self.assertFalse(
            EquippedItem.objects.filter(
                ducky=self.ducky,
                inventory_item=other_inventory,
            ).exists()
        )

    def test_equip_item_successfully(self):
        response = self.client.post(
            reverse("duckies:equip"),
            {"inventory_id": self.inventory_item.pk},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("duckies:inventory"),
        )

        self.assertTrue(
            EquippedItem.objects.filter(
                ducky=self.ducky,
                inventory_item=self.inventory_item,
            ).exists()
        )

    def test_equipping_does_not_consume_inventory(self):
        initial_quantity = self.inventory_item.quantity

        response = self.client.post(
            reverse("duckies:equip"),
            {"inventory_id": self.inventory_item.pk},
        )

        self.assertEqual(response.status_code, 302)

        self.inventory_item.refresh_from_db()

        self.assertEqual(
            self.inventory_item.quantity,
            initial_quantity,
        )

    def test_select_allowed_historical_outfit(self):
        response = self.client.post(
            reverse("duckies:select-outfit"),
            {"item_id": self.outfit.pk},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("duckies:outfits"),
        )

        self.ducky.refresh_from_db()

        self.assertEqual(
            self.ducky.selected_outfit_id,
            self.outfit.pk,
        )
