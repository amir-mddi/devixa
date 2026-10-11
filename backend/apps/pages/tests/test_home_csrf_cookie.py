from django.test import TestCase, override_settings
from django.urls import reverse


class HomeCsrfCookieTests(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_home_page_sets_csrf_cookie(self):
        response = self.client.get(reverse("pages_web:home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
