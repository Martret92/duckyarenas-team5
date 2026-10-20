from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import include, path, reverse
from django.test import override_settings
from apps.ecomotor.models import EvolutionStage
from apps.users.models import UserProfileEcomotor
from apps.duckies.models import Ducky, EvolutionItem, Item, EquipmentSlot
from apps.duckies.services import initialize_ducky, grant_item

urlpatterns = [path("duckies/", include("apps.duckies.urls"))]

@override_settings(ROOT_URLCONF=__name__)
class DuckiesViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="duckies_test", password="pass12345")
        stage = EvolutionStage.objects.create(code="STAGE_TEST", name="Etapa de prueba", ordinal=1, minimum_xp=0)
        UserProfileEcomotor.objects.create(user=cls.user, current_level=1, current_stage_code=stage.code)
        outfit = Item.objects.create(code="outfit_test", name="Vestimenta prueba", category=Item.HISTORICAL)
        EvolutionItem.objects.create(stage=stage, item=outfit)
        initialize_ducky(cls.user, "male")
        slot = EquipmentSlot.objects.create(code="TACTICAL_TEST", name="Táctico")
        cls.item = Item.objects.create(code="firewall_test", name="Firewall", category=Item.DEFENSE, slot=slot, consumable=True)
        grant_item(cls.user, cls.item, 2, "test-grant")
    def setUp(self):
        self.client.force_login(self.user)
    def test_pages(self):
        for name in ("dashboard", "inventory", "equipment", "museum", "setup"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(f"duckies:{name}")).status_code, 200)
    def test_equipping_from_inventory(self):
        inv = self.user.ducky.inventory.get(item=self.item)
        response = self.client.post(reverse("duckies:action"), {"kind": "equip", "inventory_id": inv.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.ducky.equipment.count(), 1)
    def test_get_cannot_equip(self):
        self.assertEqual(self.client.get(reverse("duckies:action")).status_code, 405)
    def test_anonymous_redirect(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("duckies:dashboard")).status_code, 302)
    def test_cross_user_inventory_cannot_be_equipped(self):
        other = get_user_model().objects.create_user(username="other")
        self.assertEqual(self.client.post(reverse("duckies:action"), {"kind": "equip", "inventory_id": 999999}).status_code, 302)
        self.assertEqual(self.user.ducky.equipment.count(), 0)
