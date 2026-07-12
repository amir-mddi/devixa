from django.core.cache import cache

from dealio.apps.common.helpers.metaclasses.singleton import Singleton


class IsolatedServiceTestMixin:
    """Prevents singleton/cache state from leaking between unit tests."""

    def setUp(self):
        super().setUp()
        Singleton._instances.clear()
        cache.clear()

    def tearDown(self):
        cache.clear()
        Singleton._instances.clear()
        super().tearDown()
