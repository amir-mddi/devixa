from django.conf import settings
from django.core.management import BaseCommand, CommandError

from backend.apps.common.logic.runtime_config_logic import RuntimeConfigCheckLogic


class Command(BaseCommand):
    help = "Validate startup configuration without contacting external services."

    def handle(self, *args, **options):
        result = RuntimeConfigCheckLogic().execute(settings)

        for line in result.summary:
            self.stdout.write(line)
        for warning in result.warnings:
            self.stdout.write(self.style.WARNING(f"WARNING: {warning}"))

        if result.errors:
            formatted_errors = "\n".join(f"- {error}" for error in result.errors)
            raise CommandError(f"Runtime configuration is invalid:\n{formatted_errors}")

        self.stdout.write(self.style.SUCCESS("Runtime configuration is valid."))
