from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AssetKind(StrEnum):
    CSS = "css"
    JAVASCRIPT = "javascript"


@dataclass(frozen=True, slots=True)
class AssetBundleDefinition:
    name: str
    kind: AssetKind
    output_relative_path: str
    source_relative_paths: tuple[str, ...]


class FrontendAssetBundleVO:
    """Single source of truth for production frontend bundles."""

    CRITICAL_CSS = AssetBundleDefinition(
        name="critical-css",
        kind=AssetKind.CSS,
        output_relative_path="app/assets/dist/critical.bundle.css",
        source_relative_paths=(
            "app/assets/Styles/variables.css",
            "app/assets/Styles/fonts.css",
            "app/assets/Styles/reset.css",
            "app/assets/Styles/framework.css",
            "app/assets/Styles/critical.css",
        ),
    )

    SITE_CSS = AssetBundleDefinition(
        name="site-css",
        kind=AssetKind.CSS,
        output_relative_path="app/assets/dist/site.bundle.css",
        source_relative_paths=(
            "app/assets/Styles/components.css",
            "app/assets/Styles/theme.css",
            "app/assets/Styles/premium.css",
            "app/assets/Styles/responsive.css",
            "app/assets/Styles/design-system-fixes.css",
            "app/assets/Styles/mobile-theme-system.css",
            "app/assets/Styles/app-ui.css",
        ),
    )

    SITE_JS = AssetBundleDefinition(
        name="site-js",
        kind=AssetKind.JAVASCRIPT,
        output_relative_path="app/assets/dist/site.bundle.js",
        source_relative_paths=(
            "app/assets/js/main.js",
            "app/assets/js/theme.js",
            "app/assets/js/pwa.js",
        ),
    )

    AUTH_CSS = AssetBundleDefinition(
        name="auth-css",
        kind=AssetKind.CSS,
        output_relative_path="app/assets/dist/auth.bundle.css",
        source_relative_paths=(
            "app/assets/Styles/variables.css",
            "app/assets/Styles/fonts.css",
            "app/assets/Styles/reset.css",
            "app/assets/Styles/framework.css",
            "app/assets/Styles/forget_password.css",
            "app/assets/Styles/app-ui.css",
        ),
    )

    HOME_CSS = AssetBundleDefinition(
        name="home-css",
        kind=AssetKind.CSS,
        output_relative_path="app/assets/dist/home.bundle.css",
        source_relative_paths=(
            "app/assets/Styles/home.css",
            "app/assets/Styles/courses.css",
            "app/assets/Styles/home-v2.css",
            "app/assets/Styles/home-v3.css",
            "app/assets/Styles/home-v4.css",
        ),
    )

    COURSES_CSS = AssetBundleDefinition(
        name="courses-css",
        kind=AssetKind.CSS,
        output_relative_path="app/assets/dist/courses.bundle.css",
        source_relative_paths=(
            "app/assets/Styles/courses.css",
            "app/assets/Styles/courses-v2.css",
        ),
    )

    COURSE_DETAIL_CSS = AssetBundleDefinition(
        name="course-detail-css",
        kind=AssetKind.CSS,
        output_relative_path="app/assets/dist/course-detail.bundle.css",
        source_relative_paths=(
            "app/assets/Styles/single_course.css",
            "app/assets/Styles/courses.css",
            "app/assets/Styles/course-detail-polish.css",
        ),
    )

    ROADMAPS_CSS = AssetBundleDefinition(
        name="roadmaps-css",
        kind=AssetKind.CSS,
        output_relative_path="app/assets/dist/roadmaps.bundle.css",
        source_relative_paths=(
            "app/assets/Styles/roadmaps.css",
            "app/assets/Styles/roadmaps-v2.css",
        ),
    )

    ABOUT_CSS = AssetBundleDefinition(
        name="about-css",
        kind=AssetKind.CSS,
        output_relative_path="app/assets/dist/about.bundle.css",
        source_relative_paths=(
            "app/assets/Styles/about_us.css",
            "app/assets/Styles/about_us-v2.css",
        ),
    )

    @classmethod
    def all(cls) -> tuple[AssetBundleDefinition, ...]:
        return (
            cls.CRITICAL_CSS,
            cls.SITE_CSS,
            cls.SITE_JS,
            cls.AUTH_CSS,
            cls.HOME_CSS,
            cls.COURSES_CSS,
            cls.COURSE_DETAIL_CSS,
            cls.ROADMAPS_CSS,
            cls.ABOUT_CSS,
        )
