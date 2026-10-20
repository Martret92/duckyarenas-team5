from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.ecomotor.models import EvolutionStage
from apps.users.models import UserProfileEcomotor
from apps.duckies.models import EvolutionItem, Item, EquipmentSlot, InventoryItem, ItemUsage
from apps.duckies.services import initialize_ducky, grant_item, equip_item, consume_item, sync_historical_outfit

class DuckiesServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="service_user")
        self.stage = EvolutionStage.objects.create(code="TEST", name="Test", ordinal=1, minimum_xp=0)
        UserProfileEcomotor.objects.create(user=self.user, current_level=1, current_stage_code=self.stage.code)
        self.outfit = Item.objects.create(code="outfit_test", name="Traje", category=Item.HISTORICAL)
        EvolutionItem.objects.create(stage=self.stage, item=self.outfit)
        self.ducky = initialize_ducky(self.user, "female")
        slot = EquipmentSlot.objects.create(code="TACTICAL", name="Táctico")
        self.item = Item.objects.create(code="firewall", name="Escudo", category=Item.DEFENSE, consumable=True, slot=slot)
    def test_initialize_idempotent(self):
        self.assertEqual(initialize_ducky(self.user, "female").pk, self.ducky.pk)
    def test_grant_idempotent(self):
        grant_item(self.user, self.item, 2, "g1")
        grant_item(self.user, self.item, 2, "g1")
        self.assertEqual(InventoryItem.objects.get(ducky=self.ducky, item=self.item).quantity, 2)
    def test_equip_does_not_consume(self):
        grant_item(self.user, self.item, 2, "g1")
        equip_item(self.user, self.item)
        self.assertEqual(InventoryItem.objects.get(ducky=self.ducky, item=self.item).quantity, 2)
    def test_consumption_requires_server(self):
        grant_item(self.user, self.item, 2, "g1")
        equip_item(self.user, self.item)
        with self.assertRaises(ValueError):
            consume_item(self.user, self.item, 1, "use1", game_reference="game1")
        self.assertEqual(ItemUsage.objects.count(), 0)
    def test_consumption_idempotent(self):
        grant_item(self.user, self.item, 2, "g1")
        equip_item(self.user, self.item)
        consume_item(self.user, self.item, 1, "use1", game_reference="game1", server_accepted=True)
        consume_item(self.user, self.item, 1, "use1", game_reference="game1", server_accepted=True)
        self.assertEqual(InventoryItem.objects.get(ducky=self.ducky, item=self.item).quantity, 1)
    def test_sync_current_stage(self):
        self.assertEqual(sync_historical_outfit(self.user).selected_outfit_id, self.outfit.pk)
