from types import SimpleNamespace

import jwt
from django.test import RequestFactory, SimpleTestCase, override_settings

from dealio.apps.permissions.access_control import AccessLimitPermission


class AccessLimitPermissionTests(SimpleTestCase):
    def _request(self, *, role="admin", method="GET", is_superuser=False):
        token = jwt.encode({"role": role}, "test-signing-key-with-at-least-32-bytes", algorithm="HS256")
        request = RequestFactory().generic(method, "/", HTTP_AUTHORIZATION=f"Bearer {token}")
        request.user = SimpleNamespace(
            is_active=True,
            is_authenticated=True,
            is_superuser=is_superuser,
        )
        return request

    @override_settings(PERMISSIONS=["admin|SampleView|get|any"])
    def test_allows_matching_role_view_method_and_scope(self):
        view = type("SampleView", (), {})()

        self.assertTrue(AccessLimitPermission().has_permission(self._request(), view))

    @override_settings(PERMISSIONS=[])
    def test_superuser_is_allowed_even_without_explicit_permission(self):
        view = type("SampleView", (), {})()

        self.assertTrue(AccessLimitPermission().has_permission(self._request(is_superuser=True), view))

    @override_settings(PERMISSIONS=["admin|OtherView|get|any"])
    def test_denies_non_matching_view(self):
        view = type("SampleView", (), {})()

        self.assertFalse(AccessLimitPermission().has_permission(self._request(), view))
