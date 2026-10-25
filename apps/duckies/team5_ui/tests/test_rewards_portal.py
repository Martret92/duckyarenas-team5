from django.test import SimpleTestCase, override_settings
from django.urls import reverse, resolve


class RewardsPortalTests(SimpleTestCase):
    @override_settings(DEBUG=True, ALLOWED_HOSTS=["127.0.0.1", "localhost"])
    def test_rewards_page_links_to_real_isolated_lab(self):
        # The portal must never invoke Jaime's coordinator against Team5 SQLite.
        from unittest.mock import patch
        with patch("apps.duckies.team5_ui.views.demo_user") as user, patch("apps.duckies.team5_ui.views.state", return_value={}):
            user.return_value = object()
            response = self.client.get(reverse("team5_ui:rewards"), HTTP_HOST="127.0.0.1:8000")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "127.0.0.1:8002/demo/objetivo-persistente/")
        self.assertContains(response, "distintas de tu Ducky medieval")

    def test_rewards_route_resolves(self):
        self.assertEqual(resolve("/team5/rewards/").url_name, "rewards")
