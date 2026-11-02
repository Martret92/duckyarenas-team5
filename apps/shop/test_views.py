from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import include, path, reverse

from apps.bank.models import Transaction, Wallet
from apps.bank.services import credit_coins
from apps.duckies.models import Ducky, InventoryItem, Item, ItemGrant, ItemLevel

from .models import Purchase, ShopItem

urlpatterns = [
    path("duckies/", include("apps.duckies.urls")),
    path("bank/", include("apps.bank.urls")),
    path("shop/", include("apps.shop.urls")),
]


@override_settings(ROOT_URLCONF=__name__)
class ShopHTTPTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="shop-http-owner")
        self.ducky = Ducky.objects.create(user=self.user, sex="male")
        self.wallet = Wallet.objects.create(user=self.user)
        self.item = Item.objects.create(
            code="http-smoke",
            name="Smoke",
            category=Item.ATTACK,
            consumable=True,
            is_active=True,
        )
        self.level = ItemLevel.objects.create(
            item=self.item,
            level=2,
            effect_code="SMOKE",
            effect_value="5",
        )
        self.offer = ShopItem.objects.create(
            code="http-smoke-pack",
            item=self.item,
            item_level=self.level,
            name="Smoke pack",
            description="A test pack",
            price_coins=20,
            included_quantity=3,
        )
        credit_coins(
            self.user,
            100,
            source="rewards",
            operation_key="shop-http-initial-credit",
        )
        self.client.force_login(self.user)

    def test_catalog_shows_only_available_active_valid_offers(self):
        self.offer.is_available = False
        self.offer.save(update_fields=("is_available", "updated_at"))
        inactive_item = Item.objects.create(
            code="inactive-http-item",
            name="Inactive",
            category=Item.HINT,
            consumable=True,
            is_active=False,
        )
        ShopItem.objects.create(
            code="inactive-http-offer",
            item=inactive_item,
            name="Inactive offer",
            price_coins=5,
        )

        response = self.client.get(reverse("shop:catalog"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Smoke pack")
        self.assertNotContains(response, "Inactive offer")

    def test_product_detail_issues_a_hidden_operation_key_and_never_accepts_price(self):
        response = self.client.get(reverse("shop:detail", args=(self.offer.code,)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="operation_key"')
        self.assertContains(response, "20 DukiCoins")
        self.assertNotContains(response, 'name="price_coins"')

    def test_purchase_uses_server_price_and_redirects_to_private_history(self):
        response = self.client.post(
            reverse("shop:purchase", args=(self.offer.code,)),
            {
                "operation_key": "http-order-001",
                "quantity": "2",
                "price_coins": "1",
            },
        )

        self.assertRedirects(response, reverse("shop:purchase-history"))
        purchase = Purchase.objects.get(user=self.user)
        self.wallet.refresh_from_db()
        inventory = InventoryItem.objects.get(
            ducky=self.ducky,
            item=self.item,
            item_level=self.level,
        )
        self.assertEqual(purchase.unit_price_coins, 20)
        self.assertEqual(purchase.total_price_coins, 40)
        self.assertEqual(purchase.bank_transaction.amount, -40)
        self.assertEqual(self.wallet.available_balance, 60)
        self.assertEqual(inventory.quantity, 6)

    def test_replayed_post_does_not_duplicate_charge_purchase_or_delivery(self):
        payload = {"operation_key": "http-order-replay", "quantity": "1"}
        url = reverse("shop:purchase", args=(self.offer.code,))

        first = self.client.post(url, payload)
        replay = self.client.post(url, payload)

        self.assertEqual(first.status_code, 302)
        self.assertEqual(replay.status_code, 302)
        self.assertEqual(Purchase.objects.filter(user=self.user).count(), 1)
        self.assertEqual(
            Transaction.objects.filter(wallet=self.wallet, amount__lt=0).count(),
            1,
        )
        self.assertEqual(ItemGrant.objects.filter(ducky=self.ducky).count(), 1)

    def test_replayed_post_succeeds_after_offer_is_disabled(self):
        payload = {
            "operation_key": "http-order-disabled-replay",
            "quantity": "1",
        }
        url = reverse("shop:purchase", args=(self.offer.code,))

        first = self.client.post(url, payload)
        self.assertEqual(first.status_code, 302)

        self.offer.is_available = False
        self.offer.save(update_fields=("is_available", "updated_at"))

        replay = self.client.post(url, payload)

        self.assertEqual(replay.status_code, 302)
        self.assertRedirects(replay, reverse("shop:purchase-history"))
        self.assertEqual(Purchase.objects.filter(user=self.user).count(), 1)
        self.assertEqual(
            Transaction.objects.filter(wallet=self.wallet, amount__lt=0).count(),
            1,
        )
        self.assertEqual(ItemGrant.objects.filter(ducky=self.ducky).count(), 1)

    def test_insufficient_funds_returns_conflict_without_purchase_or_delivery(self):
        self.wallet.available_balance = 0
        self.wallet.save(update_fields=("available_balance", "updated_at"))

        response = self.client.post(
            reverse("shop:purchase", args=(self.offer.code,)),
            {"operation_key": "http-order-poor", "quantity": "1"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertContains(response, "insufficient", status_code=409)
        self.assertFalse(Purchase.objects.filter(user=self.user).exists())
        self.assertFalse(ItemGrant.objects.filter(ducky=self.ducky).exists())

    def test_purchase_history_is_scoped_to_authenticated_user(self):
        self.client.post(
            reverse("shop:purchase", args=(self.offer.code,)),
            {"operation_key": "http-order-private", "quantity": "1"},
        )
        other = get_user_model().objects.create_user(username="shop-http-other")
        Ducky.objects.create(user=other, sex="female")
        Wallet.objects.create(user=other)
        credit_coins(
            other,
            100,
            source="rewards",
            operation_key="shop-http-other-credit",
        )
        self.client.force_login(other)

        response = self.client.get(reverse("shop:purchase-history"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["purchases"].count(), 0)
        self.assertNotContains(response, "Smoke pack")

    def test_purchase_requires_authentication(self):
        self.client.logout()

        response = self.client.post(
            reverse("shop:purchase", args=(self.offer.code,)),
            {"operation_key": "anonymous-order", "quantity": "1"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Purchase.objects.exists())

    def test_purchase_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        url = reverse("shop:detail", args=(self.offer.code,))
        csrf_client.get(url)

        response = csrf_client.post(
            reverse("shop:purchase", args=(self.offer.code,)),
            {"operation_key": "csrf-order", "quantity": "1"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Purchase.objects.exists())

    def test_invalid_quantity_is_rejected_before_service_call(self):
        response = self.client.post(
            reverse("shop:purchase", args=(self.offer.code,)),
            {"operation_key": "invalid-quantity", "quantity": "0"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Purchase.objects.exists())
