from django.test import SimpleTestCase, RequestFactory, override_settings
from django.contrib.auth.models import AnonymousUser
from apps.team5_demo.views import authorized

class DemoIsolationTests(SimpleTestCase):
    def test_unauthenticated_denied(self):
        request = RequestFactory().post('/team5/demo/action/')
        request.user = AnonymousUser()
        self.assertFalse(authorized(request))

    @override_settings(TEAM5_DEMO_ENABLED=False)
    def test_disabled_denied(self):
        request = RequestFactory().post('/team5/demo/action/')
        request.user = AnonymousUser()
        self.assertFalse(authorized(request))
