"""Pruebas de seguridad de la interfaz oficial Team 5."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.bank.models import Transaction
from apps.duckies.models import InventoryItem
from apps.shop.models import Purchase


class Team5UISecurityTests(TestCase):
    """Verifica que las operaciones restringidas no alteran datos."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="team5_security_user",
            password="test-password-123",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_legacy_buy_action_is_forbidden(self):
        """La interfaz general no debe procesar compras."""

        purchases_before = Purchase.objects.count()
        transactions_before = Transaction.objects.count()
        inventory_before = InventoryItem.objects.count()

        response = self.client.post(
            reverse("team5_ui:action"),
            {
                "action": "buy",
                "code": "any_shop_item",
                "return_to": "shop",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Purchase.objects.count(), purchases_before)
        self.assertEqual(Transaction.objects.count(), transactions_before)
        self.assertEqual(InventoryItem.objects.count(), inventory_before)

    def test_demo_operations_are_forbidden(self):
        """XP, monedas y pistas de demo no se ejecutan aquí."""

        for operation in ("xp", "coins", "hint"):
            with self.subTest(operation=operation):
                response = self.client.post(
                    reverse("team5_ui:action"),
                    {"action": operation},
                )

                self.assertEqual(response.status_code, 403)

    def test_anonymous_user_cannot_access_actions(self):
        """Las operaciones requieren autenticación."""

        self.client.logout()

        response = self.client.post(
            reverse("team5_ui:action"),
            {"action": "buy"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
