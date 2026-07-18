from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from backend.apps.common.observability.sentry.adapter import (
    SentryMonitoringAdapter,
)
from backend.apps.common.observability.sentry.filters import (
    build_before_send,
    build_before_send_transaction,
)
from backend.apps.common.observability.sentry.initializer import initialize_sentry
from backend.apps.core_models.dtos.setup_config import SentryConfiguration


class SentryConfigurationTests(TestCase):
    def test_environment_values_are_switchable(self):
        with patch.dict(
            os.environ,
            {
                "USE_SENTRY": "true",
                "SENTRY_DSN": "https://public@example.ingest.sentry.io/1",
                "SENTRY_ENVIRONMENT": "staging",
                "SENTRY_ENABLE_TRACING": "true",
                "SENTRY_TRACES_SAMPLE_RATE": "0.25",
                "SENTRY_PROFILES_SAMPLE_RATE": "0.10",
                "SENTRY_SEND_DEFAULT_PII": "false",
            },
            clear=False,
        ):
            config = SentryConfiguration()

        self.assertTrue(config.use_sentry)
        self.assertEqual(config.environment, "staging")
        self.assertTrue(config.enable_tracing)
        self.assertEqual(config.traces_sample_rate, 0.25)
        self.assertEqual(config.profiles_sample_rate, 0.10)
        self.assertFalse(config.send_default_pii)

    def test_invalid_sample_rate_is_rejected(self):
        with self.assertRaises(ValueError):
            SentryConfiguration(traces_sample_rate=1.5)


class SentryInitializerTests(TestCase):
    @patch("backend.apps.common.observability.sentry.initializer.sentry_sdk.init")
    def test_disabled_configuration_does_not_initialize_sdk(self, init_mock):
        enabled = initialize_sentry(
            SentryConfiguration(use_sentry=False),
            project_root=Path("/tmp/project"),
        )

        self.assertFalse(enabled)
        init_mock.assert_not_called()

    def test_enabled_configuration_requires_dsn(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "SENTRY_DSN is required when USE_SENTRY=true.",
        ):
            initialize_sentry(
                SentryConfiguration(use_sentry=True, dsn=""),
                project_root=Path("/tmp/project"),
            )

    @patch(
        "backend.apps.common.observability.sentry.initializer.sentry_sdk.is_initialized",
        return_value=False,
    )
    @patch("backend.apps.common.observability.sentry.initializer.sentry_sdk.init")
    def test_enabled_configuration_uses_privacy_safe_production_options(
        self,
        init_mock,
        _is_initialized_mock,
    ):
        config = SentryConfiguration(
            use_sentry=True,
            dsn="https://public@example.ingest.sentry.io/1",
            environment="production",
            release="devixa@abc123",
            enable_tracing=False,
            traces_sample_rate=0.25,
            profiles_sample_rate=0.10,
            send_default_pii=False,
            include_local_variables=False,
            max_request_body_size="never",
        )

        enabled = initialize_sentry(config, project_root=Path("/tmp/project"))

        self.assertTrue(enabled)
        kwargs = init_mock.call_args.kwargs
        self.assertEqual(kwargs["environment"], "production")
        self.assertEqual(kwargs["release"], "devixa@abc123")
        self.assertIsNone(kwargs["traces_sample_rate"])
        self.assertIsNone(kwargs["profiles_sample_rate"])
        self.assertFalse(kwargs["send_default_pii"])
        self.assertFalse(kwargs["include_local_variables"])
        self.assertEqual(kwargs["max_request_body_size"], "never")
        self.assertEqual(kwargs["in_app_include"], ["backend"])
        self.assertEqual(len(kwargs["integrations"]), 4)


class SentryFilterTests(TestCase):
    def test_error_filter_drops_ignored_operational_path(self):
        hook = build_before_send(["/metrics", "/health"])
        event = {"request": {"url": "https://example.com/metrics"}}

        self.assertIsNone(hook(event, {}))

    def test_transaction_filter_keeps_application_route(self):
        hook = build_before_send_transaction(["/metrics"])
        event = {
            "transaction": "/courses/<slug:slug>/",
            "request": {"url": "https://example.com/courses/python/"},
        }

        self.assertIs(hook(event, {}), event)


class SentryAdapterTests(TestCase):
    @patch(
        "backend.apps.common.observability.sentry.adapter.sentry_sdk.is_initialized",
        return_value=False,
    )
    @patch("backend.apps.common.observability.sentry.adapter.sentry_sdk.capture_exception")
    def test_capture_is_noop_when_sentry_is_disabled(
        self,
        capture_mock,
        _is_initialized_mock,
    ):
        event_id = SentryMonitoringAdapter.capture_exception(RuntimeError("test"))

        self.assertIsNone(event_id)
        capture_mock.assert_not_called()

    @override_settings(SENTRY_ENABLED=False)
    def test_management_command_rejects_disabled_sentry(self):
        with self.assertRaisesMessage(CommandError, "Sentry is disabled"):
            call_command("test_sentry")

    @override_settings(
        SENTRY_ENABLED=True,
        SENTRY_FLUSH_TIMEOUT_SECONDS=3.0,
    )
    @patch(
        "backend.apps.common.management.commands.test_sentry."
        "SentryMonitoringAdapter.flush"
    )
    @patch(
        "backend.apps.common.management.commands.test_sentry."
        "SentryMonitoringAdapter.capture_exception",
        return_value="event-123",
    )
    def test_management_command_sends_controlled_event(
        self,
        capture_mock,
        flush_mock,
    ):
        from io import StringIO

        stdout = StringIO()
        call_command("test_sentry", stdout=stdout)

        capture_mock.assert_called_once()
        flush_mock.assert_called_once_with(timeout_seconds=3.0)
        self.assertIn("event-123", stdout.getvalue())
