from django.conf import settings
from .base import BaseTestCase

class TestAccess(BaseTestCase):

    def test_home_view_redirect_for_anon_user(self):
        self.client.logout()
        r = self.client.get("/")
        self.assertRedirects(r, f"{settings.LOGIN_URL}?next=/", target_status_code=301)
    
    def test_home_view_responce_for_login_user(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)