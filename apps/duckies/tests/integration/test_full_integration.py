from apps.bank.models import Transaction, TransactionType
from apps.bank.services import credit_coins
from apps.duckies.integration_services import (
    grant_xp_and_sync_outfit,
    select_initial_specialization_and_outfit,
    switch_specialization_and_outfit,
)
from apps.duckies.models import InventoryItem, ItemGrant
from apps.shop.models import Purchase
from apps.shop.services import purchase_item

from .fixtures import IntegrationFixture, STAGE_CODES


class FullPlayerJourneyTests(IntegrationFixture):
    def test_player_journey_across_all_four_apps(self):
        # Ecomotor concede XP; Duckies sincroniza la etapa y la vestimenta.
        grant_xp_and_sync_outfit(self.user, 700, "journey-xp")
        self.profile.refresh_from_db()
        self.ducky.refresh_from_db()
        self.assertEqual(self.profile.current_stage_code, STAGE_CODES[-1])
        self.assertEqual(self.ducky.selected_outfit_id, self.historical[STAGE_CODES[-1]].pk)

        # Ecomotor confirma especialización; Duckies selecciona vestimenta.
        select_initial_specialization_and_outfit(self.user, "DEVELOPER")
        self.ducky.refresh_from_db()
        self.assertEqual(self.ducky.selected_outfit_id, self.spec_outfits["DEVELOPER"].pk)
        switch_specialization_and_outfit(self.user, "GAMER", "DEVELOPER")
        self.ducky.refresh_from_db()
        self.assertEqual(self.ducky.selected_outfit_id, self.spec_outfits["GAMER"].pk)

        # Bank es propietario del saldo; Shop coordina pago y entrega Duckies.
        credit_coins(self.user, 100, source="test", operation_key="journey-reward")
        offer, item, level = self.make_offer()
        first = purchase_item(self.user, offer.code, operation_key="journey-purchase", quantity=2)
        repeated = purchase_item(self.user, offer.code, operation_key="journey-purchase", quantity=2)
        self.assertEqual(first.pk, repeated.pk)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 60)
        self.assertEqual(
            InventoryItem.objects.get(ducky=self.ducky, item=item, item_level=level).quantity, 6
        )
        self.assertEqual(Purchase.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ItemGrant.objects.filter(ducky=self.ducky, item=item).count(), 1)
        self.assertEqual(
            Transaction.objects.filter(wallet=self.wallet, transaction_type=TransactionType.PURCHASE).count(),
            1,
        )
