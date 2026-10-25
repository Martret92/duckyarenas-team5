from django.test import SimpleTestCase, RequestFactory, override_settings
from django.http import Http404
from apps.duckies.team5_ui.views import _guard

class LocalAccessTests(SimpleTestCase):
    def setUp(self):self.factory=RequestFactory()
    @override_settings(DEBUG=False)
    def test_disabled_in_production(self):
        with self.assertRaises(Http404):_guard(self.factory.get("/team5/",HTTP_HOST="localhost"))
    @override_settings(DEBUG=True,ALLOWED_HOSTS=["example.com"])
    def test_rejects_external_hostname(self):
        with self.assertRaises(Http404):_guard(self.factory.get("/team5/",HTTP_HOST="example.com"))
    @override_settings(DEBUG=True, ALLOWED_HOSTS=["127.0.0.1", "localhost"])
    def test_localhost_allowed(self):
        self.assertIsNone(
            _guard(self.factory.get("/team5/", HTTP_HOST="127.0.0.1:8000"))
        )
