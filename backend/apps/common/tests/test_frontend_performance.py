from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from backend.apps.common.web.assets.logic.asset_bundle_logic import AssetBundleLogic
from backend.apps.common.web.assets.value_objects.asset_bundle_vo import (
    AssetBundleDefinition,
    AssetKind,
)
from backend.apps.common.web.performance.middleware import (
    PublicPageCachePolicyMiddleware,
)
from backend.apps.common.web.security.middleware import SecurityHeadersMiddleware
from backend.apps.common.web.security.value_objects.security_header_vo import (
    SecurityHeaderVO,
)
from backend.apps.pages.web.pwa.views import ServiceWorkerView, WebAppManifestView


class AssetBundleLogicTests(SimpleTestCase):
    def test_bundle_build_is_deterministic_and_preserves_source_order(self):
        with TemporaryDirectory() as directory:
            static_root = Path(directory)
            first = static_root / "styles/first.css"
            second = static_root / "styles/second.css"
            first.parent.mkdir(parents=True)
            first.write_text(".first { color: red; }\n", encoding="utf-8")
            second.write_text(".second { color: blue; }\n", encoding="utf-8")

            definition = AssetBundleDefinition(
                name="test-css",
                kind=AssetKind.CSS,
                output_relative_path="dist/test.css",
                source_relative_paths=(
                    "styles/first.css",
                    "styles/second.css",
                ),
            )

            result = AssetBundleLogic(static_root).build(definition)
            content = result.output_path.read_text(encoding="utf-8")

            self.assertLess(content.index(".first"), content.index(".second"))
            self.assertEqual(result.source_count, 2)
            self.assertGreater(result.size_bytes, 0)

    def test_bundle_rejects_path_escape(self):
        with TemporaryDirectory() as directory:
            definition = AssetBundleDefinition(
                name="unsafe",
                kind=AssetKind.CSS,
                output_relative_path="../unsafe.css",
                source_relative_paths=(),
            )

            with self.assertRaises(ValueError):
                AssetBundleLogic(Path(directory)).build(definition)


class PublicPageCachePolicyMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_public_html_is_bfcache_friendly_without_shared_caching(self):
        middleware = PublicPageCachePolicyMiddleware(
            lambda request: HttpResponse("ok", content_type="text/html")
        )

        response = middleware(self.factory.get("/courses/"))

        self.assertEqual(
            response["Cache-Control"],
            "private, max-age=0, must-revalidate",
        )
        self.assertIn("Cookie", response["Vary"])

    def test_private_html_keeps_its_existing_policy(self):
        middleware = PublicPageCachePolicyMiddleware(
            lambda request: HttpResponse("ok", content_type="text/html")
        )

        response = middleware(self.factory.get("/profile/"))

        self.assertNotIn("Cache-Control", response)


class SecurityHeadersMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(
        CONTENT_SECURITY_POLICY_ENABLED=True,
        CONTENT_SECURITY_POLICY_REPORT_ONLY=False,
        IS_PROD=True,
    )
    def test_strict_csp_and_capability_headers_are_added(self):
        middleware = SecurityHeadersMiddleware(
            lambda request: HttpResponse("ok", content_type="text/html")
        )

        request = self.factory.get("/")
        response = middleware(request)
        policy = response[SecurityHeaderVO.CSP_HEADER]

        self.assertTrue(request.csp_nonce)
        self.assertIn(f"'nonce-{request.csp_nonce}'", policy)
        self.assertIn("'strict-dynamic'", policy)
        self.assertIn("object-src 'none'", policy)
        self.assertIn("base-uri 'none'", policy)
        self.assertIn("frame-ancestors 'none'", policy)
        self.assertEqual(
            response[SecurityHeaderVO.PERMISSIONS_POLICY_HEADER],
            SecurityHeaderVO.PERMISSIONS_POLICY_VALUE,
        )

    @override_settings(CONTENT_SECURITY_POLICY_ENABLED=False)
    def test_nonce_remains_available_when_csp_is_disabled_locally(self):
        middleware = SecurityHeadersMiddleware(lambda request: HttpResponse("ok"))

        request = self.factory.get("/")
        response = middleware(request)

        self.assertTrue(request.csp_nonce)
        self.assertNotIn(SecurityHeaderVO.CSP_HEADER, response)
        self.assertIn(SecurityHeaderVO.PERMISSIONS_POLICY_HEADER, response)


class ProgressiveWebAppViewsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch(
        "backend.apps.pages.web.pwa.views.get_request_project_context",
        return_value={"display_name": "Devixa"},
    )
    def test_manifest_contains_installability_fields(self, *_):
        response = WebAppManifestView()(self.factory.get("/manifest.webmanifest"))
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["display"], "standalone")
        self.assertEqual(payload["start_url"], "/?source=pwa")
        self.assertEqual(payload["scope"], "/")
        self.assertEqual(len(payload["icons"]), 2)
        self.assertTrue(all(icon["sizes"] for icon in payload["icons"]))

    def test_service_worker_only_caches_same_origin_static_get_requests(self):
        response = ServiceWorkerView()(self.factory.get("/service-worker.js"))
        script = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertIn("request.method !== 'GET'", script)
        self.assertIn("url.origin !== self.location.origin", script)
        self.assertIn("url.pathname.startsWith(STATIC_PREFIX)", script)
        self.assertIn("no-cache", response["Cache-Control"])
