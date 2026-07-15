from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from backend.apps.common.web.assets.logic.asset_bundle_logic import AssetBundleLogic
from backend.apps.common.web.assets.value_objects.asset_bundle_vo import FrontendAssetBundleVO


class Command(BaseCommand):
    help = "Build deterministic CSS and JavaScript bundles from source static assets."

    def handle(self, *args, **options):
        static_root = Path(settings.BASE_DIR) / "backend" / "static"
        logic = AssetBundleLogic(static_root=static_root)

        try:
            results = [logic.build(bundle) for bundle in FrontendAssetBundleVO.all()]
        except (FileNotFoundError, ValueError, OSError) as exc:
            raise CommandError(str(exc)) from exc

        for result in results:
            relative = result.output_path.relative_to(static_root)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Built {result.name}: {relative} "
                    f"({result.source_count} sources, {result.size_bytes} bytes)"
                )
            )
