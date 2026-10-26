from unittest.mock import patch, sentinel
from django.test import SimpleTestCase
from apps.duckies.team5_ui.demo_services import grant_demo_hint
from apps.duckies.models import Item


class LocalHintTests(SimpleTestCase):
    @patch("apps.duckies.team5_ui.demo_services.grant_item")
    @patch("apps.duckies.team5_ui.demo_services.Item.objects.get_or_create")
    def test_uses_existing_duckies_service_with_traceable_source(self, get_or_create, grant):
        item = Item(code="team5_local_hint", category=Item.HINT, consumable=True)
        get_or_create.return_value = (item, True)
        grant.return_value = sentinel.delivery
        result = grant_demo_hint(sentinel.user, "hint-test-1")
        self.assertIs(result, sentinel.delivery)
        grant.assert_called_once_with(
            sentinel.user, item, 1, "hint-test-1",
            reference_type="TEAM5_LOCAL_DEMO", reference_id="manual-hint",
        )

    @patch("apps.duckies.team5_ui.demo_services.grant_item")
    @patch("apps.duckies.team5_ui.demo_services.Item.objects.get_or_create")
    def test_rejects_conflicting_catalog_item(self, get_or_create, grant):
        get_or_create.return_value = (Item(code="team5_local_hint", category=Item.ATTACK), False)
        with self.assertRaises(ValueError):
            grant_demo_hint(sentinel.user, "hint-test-2")
        grant.assert_not_called()
