"""Pruebas de seguridad de la interfaz oficial Team 5."""

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.middleware.csrf import get_token
from django.test import Client, TestCase
from django.urls import reverse

from apps.bank.models import Transaction, Wallet
from apps.duckies.models import (
    Ducky, EquipmentHistory, EquipmentSlot, EquippedItem, InventoryItem,
    Item, ItemGrant, ItemLevel,
)
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

    def _make_unowned_equipment(self):
        Ducky.objects.create(user=self.user, sex="male")
        slot = EquipmentSlot.objects.create(
            code="team5-security-slot", name="Ranura de prueba",
        )
        item = Item.objects.create(
            code="team5-security-item", name="Artículo sin posesión",
            category=Item.ATTACK, consumable=True, slot=slot,
        )
        level = ItemLevel.objects.create(item=item, level=1)
        return item, level

    @staticmethod
    def _business_counts():
        return tuple(model.objects.count() for model in (
            InventoryItem, EquippedItem, EquipmentHistory, ItemGrant,
            Wallet, Transaction, Purchase,
        ))

    def test_unowned_equipment_returns_409_with_valid_csrf_without_writes(self):
        item, level = self._make_unowned_equipment()
        before = self._business_counts()

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        request = HttpRequest()
        csrf_token = get_token(request)
        client.cookies["csrftoken"] = request.META["CSRF_COOKIE"]

        response = client.post(
            reverse("team5_ui:action"),
            {
                "action": "equip", "item_id": str(item.pk),
                "code": str(level.pk), "return_to": "inventory",
            },
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 409)
        self.assertContains(
            response, "El artículo no está disponible en tu inventario.",
            status_code=409,
        )
        self.assertNotContains(response, "InventoryItem", status_code=409)
        self.assertNotContains(response, "DoesNotExist", status_code=409)
        self.assertEqual(self._business_counts(), before)

    def test_unowned_equipment_without_csrf_returns_403_without_writes(self):
        item, level = self._make_unowned_equipment()
        before = self._business_counts()

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(
            reverse("team5_ui:action"),
            {"action": "equip", "item_id": str(item.pk), "code": str(level.pk)},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self._business_counts(), before)

    def test_owned_equipment_still_uses_existing_service(self):
        item, level = self._make_unowned_equipment()
        ducky = Ducky.objects.get(user=self.user)
        owned = InventoryItem.objects.create(
            ducky=ducky, item=item, item_level=level, quantity=1,
        )

        response = self.client.post(
            reverse("team5_ui:action"),
            {
                "action": "equip", "item_id": str(item.pk),
                "code": str(level.pk), "return_to": "inventory",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("team5_ui:inventory"))
        self.assertTrue(EquippedItem.objects.filter(
            ducky=ducky, inventory_item=owned, slot=item.slot,
        ).exists())
        self.assertEqual(EquipmentHistory.objects.filter(
            ducky=ducky, item=item, action="EQUIP",
        ).count(), 1)
        owned.refresh_from_db()
        self.assertEqual(owned.quantity, 1)

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
