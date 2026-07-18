from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from backend.apps.common.logic.frontend_assets_logic import FrontendAssetsBuildLogic


class Command(BaseCommand):
    help = "Validate the project's source-managed frontend assets."

    def handle(self, *args, **options):
        static_dirs = tuple(getattr(settings, "STATICFILES_DIRS", ()) or ())
        if not static_dirs:
            raise CommandError("STATICFILES_DIRS is empty.")

        try:
            result = FrontendAssetsBuildLogic().execute(
                static_source_root=Path(static_dirs[0]),
                asset_root=str(settings.PROJECT_STATIC_ASSET_ROOT),
            )
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Frontend assets are ready: "
                f"{len(result.checked_files)} required files validated under "
                f"{result.asset_root}."
            )
        )
