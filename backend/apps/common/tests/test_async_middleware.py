from __future__ import annotations

from asgiref.sync import iscoroutinefunction
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from backend.apps.common.helpers.middlewares.block_token import BlockedTokenMiddleware
from backend.apps.common.helpers.middlewares.general_response import GeneralResponseMiddleware
from backend.apps.common.helpers.middlewares.response_metrics import ResponseMetricsMiddleware
from backend.apps.common.web.ajax.middleware import AjaxFormRedirectMiddleware
from backend.apps.common.web.seo.enums.seo_enums import SeoRobotsDirectiveEnum
from backend.apps.common.web.seo.middleware import SeoRobotsHeaderMiddleware
from backend.project.middleware import PrimaryAfterWriteMiddleware


class AsyncMiddlewareCompatibilityTests(SimpleTestCase):
    middleware_classes = (
        SeoRobotsHeaderMiddleware,
        AjaxFormRedirectMiddleware,
        ResponseMetricsMiddleware,
        GeneralResponseMiddleware,
        BlockedTokenMiddleware,
        PrimaryAfterWriteMiddleware,
    )

    async def test_custom_middleware_preserves_async_chain(self):
        request = RequestFactory().get("/health/")

        async def get_response(_request):
            return HttpResponse("ok")

        for middleware_class in self.middleware_classes:
            with self.subTest(middleware=middleware_class.__name__):
                middleware = middleware_class(get_response)
                self.assertTrue(iscoroutinefunction(middleware))
                response = await middleware(request)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b"ok")

    def test_custom_middleware_preserves_sync_chain(self):
        request = RequestFactory().get("/health/")

        def get_response(_request):
            return HttpResponse("ok")

        for middleware_class in self.middleware_classes:
            with self.subTest(middleware=middleware_class.__name__):
                middleware = middleware_class(get_response)
                self.assertFalse(iscoroutinefunction(middleware))
                response = middleware(request)
                self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=True)
    async def test_seo_header_is_applied_in_async_mode(self):
        request = RequestFactory().get("/admin/private/")

        async def get_response(_request):
            return HttpResponse("ok")

        response = await SeoRobotsHeaderMiddleware(get_response)(request)
        self.assertEqual(
            response["X-Robots-Tag"],
            SeoRobotsDirectiveEnum.NOINDEX.value,
        )


class AjaxFormRedirectMiddlewareTests(SimpleTestCase):
    async def test_ajax_post_redirect_becomes_json_contract(self):
        request = RequestFactory().post(
            "/basket/add/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_X_AJAX_FORM="true",
        )

        async def get_response(_request):
            response = HttpResponse(status=302)
            response["Location"] = "/profile/#courses"
            return response

        response = await AjaxFormRedirectMiddleware(get_response)(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"success": True, "redirect_url": "/profile/#courses"},
        )

    def test_regular_post_redirect_is_not_changed(self):
        request = RequestFactory().post("/basket/add/")

        def get_response(_request):
            response = HttpResponse(status=302)
            response["Location"] = "/basket/"
            return response

        response = AjaxFormRedirectMiddleware(get_response)(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/basket/")

    def test_method_preserving_redirect_is_not_rewritten(self):
        request = RequestFactory().post(
            "/provider/continue/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_X_AJAX_FORM="true",
        )

        def get_response(_request):
            response = HttpResponse(status=307)
            response["Location"] = "/provider/finalize/"
            return response

        response = AjaxFormRedirectMiddleware(get_response)(request)
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response["Location"], "/provider/finalize/")
