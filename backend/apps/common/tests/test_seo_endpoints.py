from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from backend.apps.common.web.seo.value_objects.seo_vo import SeoRouteVO


class SeoEndpointTests(TestCase):
    def test_sitemap_renders_without_select_related_deferred_field_conflict(self):
        response = self.client.get(reverse(SeoRouteVO.SITEMAP.value))

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/xml; charset=utf-8", response["Content-Type"])
        self.assertContains(response, "<urlset")
