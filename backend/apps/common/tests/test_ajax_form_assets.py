from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase


BACKEND_ROOT = Path(__file__).resolve().parents[3]


class AjaxFormAssetTests(SimpleTestCase):
    def test_jquery_build_contains_ajax_module(self):
        jquery = (
            BACKEND_ROOT
            / "static"
            / "app"
            / "assets"
            / "vendor"
            / "jquery"
            / "jquery-3.7.1.min.js"
        ).read_text(encoding="utf-8")
        self.assertIn("jQuery v3.7.1", jquery)
        self.assertIn("ajax", jquery)
        self.assertNotIn("-ajax,-ajax/jsonp", jquery[:200])

    def test_ajax_form_controller_uses_jquery_ajax_and_csrf_header(self):
        source = (
            BACKEND_ROOT
            / "static"
            / "app"
            / "assets"
            / "js"
            / "ajax_forms.js"
        ).read_text(encoding="utf-8")
        self.assertIn("$.ajax", source)
        self.assertIn('"X-CSRFToken"', source)
        self.assertIn('$(document).on("submit.devixaAjaxForms"', source)
        self.assertIn("new FormData", source)
        self.assertIn("applyHtmlDocument", source)
        self.assertIn("bootInitialModules", source)
        self.assertIn('script[type="application/ld+json"]', source)

    def test_base_template_loads_local_jquery_and_ajax_controller(self):
        template = (
            BACKEND_ROOT / "templates" / "web" / "pages" / "base.html"
        ).read_text(encoding="utf-8")
        self.assertIn("vendor/jquery/jquery-3.7.1.min.js", template)
        self.assertIn("js/ajax_forms.js", template)
        self.assertIn('data-ajax-module="main"', template)
        self.assertIn('type="application/x-devixa-ajax-module"', template)

    def test_auth_template_loads_same_ajax_runtime(self):
        template = (
            BACKEND_ROOT / "templates" / "web" / "accounts" / "auth_base.html"
        ).read_text(encoding="utf-8")
        self.assertIn("vendor/jquery/jquery-3.7.1.min.js", template)
        self.assertIn("js/ajax_forms.js", template)
        self.assertIn('data-ajax-module="auth"', template)
        self.assertIn('data-ajax-module="auth-theme-bootstrap"', template)
        self.assertIn('type="application/x-devixa-ajax-module"', template)


class AjaxPageLifecycleAssetTests(SimpleTestCase):
    def test_reveal_effects_initialize_after_dom_content_loaded(self):
        source = (
            BACKEND_ROOT
            / "static"
            / "app"
            / "assets"
            / "js"
            / "effects.js"
        ).read_text(encoding="utf-8")

        self.assertIn('document.readyState === "loading"', source)
        self.assertIn("initializeEffects();", source)
        self.assertIn("observer.unobserve(entry.target)", source)
        self.assertNotIn("entry.target.classList.remove", source)

    def test_reveal_css_has_progressive_enhancement_fallback(self):
        source = (
            BACKEND_ROOT
            / "static"
            / "app"
            / "assets"
            / "Styles"
            / "components.css"
        ).read_text(encoding="utf-8")

        self.assertIn("html.reveal-pending .reveal:not(.activee)", source)
        self.assertIn("html.reveal-ready .reveal_left:not(.activee)", source)
        self.assertIn("@media (prefers-reduced-motion:reduce)", source)

    def test_ajax_runtime_preserves_server_style_order(self):
        source = (
            BACKEND_ROOT
            / "static"
            / "app"
            / "assets"
            / "js"
            / "ajax_forms.js"
        ).read_text(encoding="utf-8")

        self.assertIn("MANAGED_STYLE_SELECTOR", source)
        self.assertIn("data-ajax-managed-style", source)
        self.assertIn("data-ajax-style-boundary", source)
        self.assertIn("document.head.insertBefore(styleNode", source)
        self.assertIn("prepareRevealLifecycle(moduleScripts)", source)
        self.assertIn('root.classList.add("reveal-pending")', source)

    def test_all_template_inline_styles_are_ajax_managed(self):
        templates_root = BACKEND_ROOT / "templates" / "web"
        unmanaged = []

        for path in templates_root.rglob("*.html"):
            source = path.read_text(encoding="utf-8")
            if "<style" in source and "<style data-ajax-managed-style" not in source:
                unmanaged.append(str(path.relative_to(templates_root)))

        self.assertEqual([], unmanaged)

    def test_home_slider_never_scrolls_the_document_during_initialization(self):
        home_source = (
            BACKEND_ROOT / "static" / "app" / "assets" / "js" / "home.js"
        ).read_text(encoding="utf-8")
        main_source = (
            BACKEND_ROOT / "static" / "app" / "assets" / "js" / "main.js"
        ).read_text(encoding="utf-8")

        self.assertIn("track.scrollTo", home_source)
        self.assertNotIn("scrollIntoView", home_source)
        self.assertNotIn("testimonial_track", main_source)

    def test_premium_metrics_are_registered_before_reveal_observer(self):
        source = (
            BACKEND_ROOT / "static" / "app" / "assets" / "js" / "premium.js"
        ).read_text(encoding="utf-8")

        self.assertIn("'[data-premium-reveal]'", source)
        self.assertLess(source.index("polishCourseMetrics();"), source.index("revealEverything();"))
