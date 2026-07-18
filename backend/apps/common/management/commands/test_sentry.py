from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from backend.apps.common.observability.sentry.adapter import (
    SentryMonitoringAdapter,
)
from backend.apps.common.observability.sentry.value_objects import (
    SentryComponentVO,
    SentryTagVO,
)


class Command(BaseCommand):
    help = "Send a controlled test exception to the configured Sentry project."

    def handle(self, *args, **options):
        del args, options
        if not getattr(settings, "SENTRY_ENABLED", False):
            raise CommandError(
                "Sentry is disabled. Set USE_SENTRY=true and configure SENTRY_DSN."
            )

        try:
            raise RuntimeError("Devixa controlled Sentry integration test")
        except RuntimeError as exception:
            event_id = SentryMonitoringAdapter.capture_exception(
                exception,
                tags={
                    SentryTagVO.COMPONENT: SentryComponentVO.MANAGEMENT_COMMAND,
                    SentryTagVO.TEST_EVENT: True,
                },
            )

        timeout = float(
            getattr(settings, "SENTRY_FLUSH_TIMEOUT_SECONDS", 5.0)
        )
        SentryMonitoringAdapter.flush(timeout_seconds=timeout)

        if not event_id:
            raise CommandError("Sentry did not return an event ID.")

        self.stdout.write(
            self.style.SUCCESS(f"Sentry test event sent. Event ID: {event_id}")
        )
