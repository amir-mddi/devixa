from types import SimpleNamespace

from django.test import RequestFactory, SimpleTestCase, override_settings

from dealio.apps.permissions.access_control import AccessLimitPermission


class AccessLimitPermissionTests(SimpleTestCase):
    def _request(self, *, role="admin", method="GET", is_superuser=False, forged_role=None):
        headers = {}
        if forged_role:
            headers["HTTP_AUTHORIZATION"] = f"Bearer forged-{forged_role}"
        request = RequestFactory().generic(method, "/", **headers)
        request.user = SimpleNamespace(
            is_active=True,
            is_authenticated=True,
            is_superuser=is_superuser,
            role=SimpleNamespace(symbol=role),
        )
        return request

    @override_settings(PERMISSIONS=["admin|SampleView|get|any"])
    def test_allows_matching_database_role_view_method_and_scope(self):
        view = type("SampleView", (), {})()
        self.assertTrue(AccessLimitPermission().has_permission(self._request(), view))

    @override_settings(PERMISSIONS=["admin|SampleView|get|any"])
    def test_ignores_forged_token_role_claim(self):
        view = type("SampleView", (), {})()
        request = self._request(role="user", forged_role="admin")
        self.assertFalse(AccessLimitPermission().has_permission(request, view))

    @override_settings(PERMISSIONS=[])
    def test_superuser_is_allowed_even_without_explicit_permission(self):
        view = type("SampleView", (), {})()
        self.assertTrue(AccessLimitPermission().has_permission(self._request(is_superuser=True), view))

    @override_settings(PERMISSIONS=["admin|OtherView|get|any"])
    def test_denies_non_matching_view(self):
        view = type("SampleView", (), {})()
        self.assertFalse(AccessLimitPermission().has_permission(self._request(), view))
