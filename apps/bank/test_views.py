from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import include, path, reverse

from apps.bank.models import Transaction, Wallet
from apps.bank.services import credit_coins, debit_coins

urlpatterns = [
    path("duckies/", include("apps.duckies.urls")),
    path("bank/", include("apps.bank.urls")),
    path("shop/", include("apps.shop.urls")),
]


@override_settings(ROOT_URLCONF=__name__)
class WalletHTTPTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="wallet-owner")
        self.other = get_user_model().objects.create_user(username="wallet-other")
        self.wallet = Wallet.objects.create(user=self.user)
        self.other_wallet = Wallet.objects.create(user=self.other)
        self.client.force_login(self.user)

    def test_wallet_displays_summary_and_only_current_users_ledger(self):
        credit_coins(
            self.user,
            80,
            source="rewards",
            operation_key="wallet-http-credit",
            description="Reward for activity",
        )
        debit_coins(
            self.user,
            25,
            source="shop",
            operation_key="wallet-http-debit",
            description="Shop purchase",
        )
        credit_coins(
            self.other,
            500,
            source="rewards",
            operation_key="wallet-http-other-credit",
            description="Private other-user movement",
        )

        response = self.client.get(reverse("bank:wallet"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"], {
            "available_balance": 55,
            "total_earned": 80,
            "total_spent": 25,
        })
        self.assertEqual(response.context["transactions"].count(), 2)
        self.assertNotContains(response, "Private other-user movement")
        self.assertContains(response, "Reward for activity")

    def test_wallet_page_does_not_create_missing_wallet(self):
        self.wallet.delete()

        response = self.client.get(reverse("bank:wallet"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["wallet"])
        self.assertContains(response, "La inicialización corresponde")
        self.assertFalse(Wallet.objects.filter(user=self.user).exists())

    def test_wallet_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("bank:wallet"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("next=", response.url)

    def test_wallet_is_read_only(self):
        response = self.client.post(reverse("bank:wallet"))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Transaction.objects.count(), 0)
