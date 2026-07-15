from __future__ import annotations

from types import SimpleNamespace

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from backend.apps.common.web.seo.adapters.request_url_adapter import (
    SeoRequestUrlAdapter,
)
from backend.apps.common.web.seo.dtos.seo_dtos import (
    SeoMetadataOverrideDTO,
    SeoProjectDTO,
)
from backend.apps.common.web.seo.enums.seo_enums import SeoRobotsDirectiveEnum
from backend.apps.common.web.seo.logic.metadata_logic import SeoMetadataLogic
from backend.apps.common.web.seo.logic.structured_data_logic import (
    SeoStructuredDataLogic,
)
from backend.apps.common.web.seo.middleware import SeoRobotsHeaderMiddleware


@override_settings(
    STATIC_URL="/static/",
    SEO_CANONICAL_ORIGIN="https://acdevixa.ir",
)
class SeoMetadataLogicTestCase(TestCase):
    databases = set()

    def setUp(self):
        self.factory = RequestFactory()
        self.project = {
            "name": "devixa",
            "display_name": "Devixa",
            "description": "آموزش برنامه‌نویسی پروژه‌محور",
            "tagline": "یادگیری برای بازار کار",
            "email_domain": "acdevixa.ir",
            "contact_email": "hello@acdevixa.ir",
            "support_email": "support@acdevixa.ir",
            "phone": "",
            "address": "",
            "working_hours": "",
            "github_url": "#",
            "linkedin_url": "#",
            "telegram_url": "#",
            "instagram_url": "#",
        }

    def request_for(self, path: str, view_name: str):
        request = self.factory.get(path)
        request.resolver_match = SimpleNamespace(view_name=view_name)
        return request

    def test_public_page_is_indexable_and_canonical_query_is_removed(self):
        request = self.request_for(
            "/courses/?search=django",
            "courses_web:course_list",
        )

        seo = SeoMetadataLogic().build(
            request=request,
            project_mapping=self.project,
        )

        self.assertEqual(seo.canonical_url, "https://acdevixa.ir/courses/")
        self.assertEqual(
            seo.robots,
            SeoRobotsDirectiveEnum.NOINDEX_FOLLOW.value,
        )
        self.assertIn("دوره‌های برنامه‌نویسی", seo.title)

    def test_public_page_without_query_is_indexable(self):
        request = self.request_for("/courses/", "courses_web:course_list")

        seo = SeoMetadataLogic().build(
            request=request,
            project_mapping=self.project,
        )

        self.assertEqual(seo.robots, SeoRobotsDirectiveEnum.INDEX.value)

    def test_private_page_is_noindex_by_default(self):
        request = self.request_for("/profile/", "accounts_web:profile")

        seo = SeoMetadataLogic().build(
            request=request,
            project_mapping=self.project,
        )

        self.assertEqual(seo.robots, SeoRobotsDirectiveEnum.NOINDEX.value)

    def test_homepage_contains_website_and_organization_schema(self):
        request = self.request_for("/", "pages_web:home")

        seo = SeoMetadataLogic().build(
            request=request,
            project_mapping=self.project,
        )
        schemas = "\n".join(seo.structured_data_json)

        self.assertIn('"@type":"WebSite"', schemas)
        self.assertIn('"@type":"EducationalOrganization"', schemas)
        self.assertIn("Devixa", schemas)
        self.assertNotIn('"sameAs":[]', schemas)

    def test_override_replaces_dynamic_metadata(self):
        request = self.request_for(
            "/courses/django/",
            "courses_web:course_detail",
        )
        override = SeoMetadataOverrideDTO(
            title="Django Clean Architecture | Devixa",
            description="توضیحات اختصاصی دوره",
            canonical_path="/courses/django/",
        )

        seo = SeoMetadataLogic().build(
            request=request,
            project_mapping=self.project,
            override=override,
        )

        self.assertEqual(seo.title, override.title)
        self.assertEqual(seo.description, override.description)
        self.assertEqual(
            seo.canonical_url,
            "https://acdevixa.ir/courses/django/",
        )


@override_settings(SEO_CANONICAL_ORIGIN="")
class SeoRequestUrlAdapterTestCase(TestCase):
    databases = set()

    def test_project_domain_without_scheme_becomes_https_origin(self):
        request = RequestFactory().get("/courses/")

        adapter = SeoRequestUrlAdapter.from_project(
            request,
            {"email_domain": "acdevixa.ir"},
        )

        self.assertEqual(adapter.origin, "https://acdevixa.ir")
        self.assertEqual(
            adapter.canonical_url(),
            "https://acdevixa.ir/courses/",
        )


class SeoStructuredDataLogicTestCase(TestCase):
    databases = set()

    def test_organization_omits_empty_social_profile_list(self):
        project = SeoProjectDTO.from_mapping(
            {
                "display_name": "Devixa",
                "name": "devixa",
                "github_url": "#",
                "linkedin_url": "",
                "telegram_url": "",
                "instagram_url": "",
            }
        )

        payload = SeoStructuredDataLogic().organization(
            project=project,
            origin="https://acdevixa.ir",
            logo_url="https://acdevixa.ir/static/logo.png",
        )

        self.assertNotIn("sameAs", payload)


class SeoRobotsHeaderMiddlewareTestCase(TestCase):
    databases = set()

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SeoRobotsHeaderMiddleware(
            lambda request: HttpResponse("ok")
        )

    def test_private_path_gets_noindex_header(self):
        response = self.middleware(self.factory.get("/profile/"))

        self.assertEqual(
            response["X-Robots-Tag"],
            SeoRobotsDirectiveEnum.NOINDEX.value,
        )

    def test_public_path_does_not_get_noindex_header(self):
        response = self.middleware(self.factory.get("/courses/"))

        self.assertNotIn("X-Robots-Tag", response)
