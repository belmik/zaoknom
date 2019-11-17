from django.conf import settings
from django.urls import reverse
from .base import BaseTestCase


class TestAccess(BaseTestCase):
    def setUp(self):
        self.home_url = reverse("docbox:home")
        return super().setUp()

    def test_home_view_redirect_for_anon_user(self):
        self.client.logout()
        r = self.client.get(self.home_url)
        self.assertRedirects(
            r, f"{settings.LOGIN_URL}?next={self.home_url}", target_status_code=301
        )

    def test_home_view_responce_for_login_user(self):
        r = self.client.get(self.home_url)
        self.assertEqual(r.status_code, 200)
