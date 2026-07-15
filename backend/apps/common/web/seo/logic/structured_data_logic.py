from __future__ import annotations

from typing import Any, Iterable, Mapping

from backend.apps.common.web.seo.dtos.seo_dtos import SeoProjectDTO
from backend.apps.common.web.seo.enums.seo_enums import SeoSchemaTypeEnum
from backend.apps.common.web.seo.value_objects.seo_vo import SeoSchemaTextVO


class SeoStructuredDataLogic:
    @staticmethod
    def _clean_urls(values: Iterable[str]) -> list[str]:
        return [
            value
            for value in values
            if value
            and value != "#"
            and value.startswith(("http://", "https://"))
        ]

    def website(self, *, project: SeoProjectDTO, origin: str) -> dict[str, Any]:
        alternate_names = tuple(
            dict.fromkeys(
                value
                for value in (project.name, f"آکادمی {project.display_name}")
                if value and value != project.display_name
            )
        )
        payload: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": SeoSchemaTypeEnum.WEBSITE.value,
            "@id": f"{origin}/#website",
            "url": f"{origin}/",
            "name": project.display_name,
            "inLanguage": "fa-IR",
        }
        if alternate_names:
            payload["alternateName"] = list(alternate_names)
        return payload

    def organization(self, *, project: SeoProjectDTO, origin: str, logo_url: str) -> dict[str, Any]:
        social_urls = self._clean_urls(
            (
                project.github_url,
                project.linkedin_url,
                project.telegram_url,
                project.instagram_url,
            )
        )
        payload: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": SeoSchemaTypeEnum.EDUCATIONAL_ORGANIZATION.value,
            "@id": f"{origin}/#organization",
            "name": project.display_name,
            "alternateName": f"آکادمی {project.display_name}",
            "url": f"{origin}/",
            "logo": logo_url,
            "description": project.description or project.tagline,
        }
        if social_urls:
            payload["sameAs"] = social_urls
        if project.contact_email:
            payload["email"] = project.contact_email
        if project.phone:
            payload["telephone"] = project.phone
        if project.address:
            payload["address"] = {
                "@type": "PostalAddress",
                "streetAddress": project.address,
            }
        return payload

    def breadcrumb(self, items: Iterable[tuple[str, str]]) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": SeoSchemaTypeEnum.BREADCRUMB_LIST.value,
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": position,
                    "name": name,
                    "item": url,
                }
                for position, (name, url) in enumerate(items, start=1)
            ],
        }

    def course(
        self,
        *,
        title: str,
        description: str,
        url: str,
        provider_name: str,
        provider_url: str,
        image_url: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": SeoSchemaTypeEnum.COURSE.value,
            "name": title,
            "description": description,
            "url": url,
            "inLanguage": "fa-IR",
            "provider": {
                "@type": SeoSchemaTypeEnum.EDUCATIONAL_ORGANIZATION.value,
                "name": provider_name,
                "url": provider_url,
                "description": SeoSchemaTextVO.COURSE_PROVIDER_DESCRIPTION.value,
            },
        }
        if image_url:
            payload["image"] = image_url
        return payload

    def learning_resource(
        self,
        *,
        title: str,
        description: str,
        url: str,
        provider_name: str,
        provider_url: str,
    ) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": SeoSchemaTypeEnum.LEARNING_RESOURCE.value,
            "name": title,
            "description": description,
            "url": url,
            "inLanguage": "fa-IR",
            "provider": {
                "@type": SeoSchemaTypeEnum.EDUCATIONAL_ORGANIZATION.value,
                "name": provider_name,
                "url": provider_url,
            },
        }

    def article(
        self,
        *,
        article_type: str,
        title: str,
        description: str,
        url: str,
        publisher_name: str,
        publisher_logo_url: str,
        published_at: object | None,
        updated_at: object | None,
        image_url: str | None,
        author_name: str,
    ) -> dict[str, Any]:
        schema_type = (
            SeoSchemaTypeEnum.NEWS_ARTICLE.value
            if article_type == "news"
            else SeoSchemaTypeEnum.BLOG_POSTING.value
        )
        payload: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "headline": title,
            "description": description,
            "mainEntityOfPage": url,
            "url": url,
            "inLanguage": "fa-IR",
            "author": {"@type": "Person", "name": author_name},
            "publisher": {
                "@type": SeoSchemaTypeEnum.EDUCATIONAL_ORGANIZATION.value,
                "name": publisher_name,
                "logo": {"@type": "ImageObject", "url": publisher_logo_url},
            },
        }
        if published_at:
            payload["datePublished"] = published_at.isoformat()
        if updated_at:
            payload["dateModified"] = updated_at.isoformat()
        if image_url:
            payload["image"] = [image_url]
        return payload

    def android_application(
        self,
        *,
        name: str,
        description: str,
        url: str,
        download_url: str,
        image_url: str,
        version: str,
    ) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": SeoSchemaTypeEnum.SOFTWARE_APPLICATION.value,
            "name": name,
            "description": description,
            "url": url,
            "downloadUrl": download_url,
            "image": image_url,
            "applicationCategory": SeoSchemaTextVO.ANDROID_CATEGORY.value,
            "operatingSystem": SeoSchemaTextVO.ANDROID_OPERATING_SYSTEM.value,
            "softwareVersion": version,
            "inLanguage": "fa-IR",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "IRR"},
        }
