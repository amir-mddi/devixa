from __future__ import annotations

import json
from unittest.mock import patch

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase
from django.urls import Resolver404

from backend.apps.common.logic.http_error_logic import NotFoundErrorLogic
from backend.apps.common.vo.http_error_vo import HttpErrorCodeVO, HttpErrorTextVO
from backend.apps.common.web.error_views import page_not_found


PROJECT_CONTEXT = {
    "name": "devixa",
    "display_name": "Devixa",
    "description": "آموزش برنامه‌نویسی پروژه‌محور",
    "tagline": "یادگیری با پروژه واقعی",
    "email_domain": "acdevixa.ir",
    "contact_email": "info@acdevixa.ir",
    "support_email": "support@acdevixa.ir",
    "phone": "",
    "address": "",
    "working_hours": "",
    "github_url": "",
    "linkedin_url": "",
    "telegram_url": "",
    "instagram_url": "",
    "logo_initial": "D",
}


class NotFoundErrorLogicTests(SimpleTestCase):
    def test_unknown_route_uses_generic_public_message(self):
        error = NotFoundErrorLogic.from_exception(
            Resolver404({"path": "undefined-page/", "tried": []})
        )

        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.code, HttpErrorCodeVO.NOT_FOUND)
        self.assertEqual(error.message, HttpErrorTextVO.NOT_FOUND_MESSAGE)

    def test_missing_object_preserves_safe_domain_message(self):
        error = NotFoundErrorLogic.from_exception(
            Http404("دوره مورد نظر پیدا نشد.")
        )

        self.assertEqual(error.message, "دوره مورد نظر پیدا نشد.")

    def test_technical_object_message_is_not_exposed(self):
        error = NotFoundErrorLogic.from_exception(
            Http404("No Course matches the given query.")
        )

        self.assertEqual(error.message, HttpErrorTextVO.NOT_FOUND_OBJECT_MESSAGE)


class PageNotFoundResponseTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch(
        "backend.apps.common.context_processors.get_request_project_context",
        return_value=PROJECT_CONTEXT,
    )
    @patch(
        "backend.apps.common.web.error_views.get_request_project_context",
        return_value=PROJECT_CONTEXT,
    )
    def test_browser_404_renders_custom_page(self, *_):
        request = self.factory.get(
            "/undefined-page/",
            HTTP_ACCEPT="text/html",
            HTTP_HOST="acdevixa.ir",
        )

        response = page_not_found(
            request,
            Resolver404({"path": "undefined-page/", "tried": []}),
        )
        body = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response,
            HttpErrorTextVO.NOT_FOUND_TITLE,
            status_code=404,
        )
        self.assertIn("/undefined-page/", body)
        self.assertEqual(response["X-Robots-Tag"], "noindex,nofollow,noarchive")
        self.assertIn("no-store", response["Cache-Control"])

    @patch(
        "backend.apps.common.context_processors.get_request_project_context",
        return_value=PROJECT_CONTEXT,
    )
    @patch(
        "backend.apps.common.web.error_views.get_request_project_context",
        return_value=PROJECT_CONTEXT,
    )
    def test_missing_object_uses_same_custom_page(self, *_):
        request = self.factory.get(
            "/courses/unknown-course/",
            HTTP_ACCEPT="text/html",
            HTTP_HOST="acdevixa.ir",
        )

        response = page_not_found(
            request,
            Http404("دوره مورد نظر پیدا نشد."),
        )

        self.assertContains(
            response,
            "دوره مورد نظر پیدا نشد.",
            status_code=404,
        )

    @patch(
        "backend.apps.common.web.error_views.get_request_project_context",
        return_value=PROJECT_CONTEXT,
    )
    def test_unknown_api_route_returns_json(self, *_):
        request = self.factory.get(
            "/api/v1/courses/unknown/",
            HTTP_ACCEPT="application/json",
            HTTP_HOST="acdevixa.ir",
        )

        response = page_not_found(
            request,
            Resolver404({"path": "api/v1/courses/unknown/", "tried": []}),
        )
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(payload["code"], HttpErrorCodeVO.NOT_FOUND)
        self.assertEqual(payload["detail"], HttpErrorTextVO.NOT_FOUND_MESSAGE)
        self.assertEqual(response["X-Robots-Tag"], "noindex,nofollow,noarchive")
