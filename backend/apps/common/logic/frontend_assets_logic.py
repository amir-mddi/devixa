from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FrontendAssetsResult:
    asset_root: Path
    checked_files: tuple[Path, ...]


class FrontendAssetsBuildLogic:
    """Validate source-managed frontend assets.

    This project ships plain CSS/JavaScript files and has no Node compilation
    step. The compatibility command verifies required runtime files so startup
    scripts can fail early with an actionable error.
    """

    REQUIRED_RELATIVE_FILES = (
        Path("vendor/jquery/jquery-3.7.1.min.js"),
        Path("js/ajax_forms.js"),
        Path("js/effects.js"),
        Path("Styles/ajax-forms.css"),
    )

    def execute(self, static_source_root: Path, asset_root: str) -> FrontendAssetsResult:
        resolved_asset_root = static_source_root / asset_root
        if not resolved_asset_root.is_dir():
            raise FileNotFoundError(
                f"Frontend asset root does not exist: {resolved_asset_root}"
            )

        checked_files = tuple(
            resolved_asset_root / relative_path
            for relative_path in self.REQUIRED_RELATIVE_FILES
        )
        missing_files = [path for path in checked_files if not path.is_file()]
        if missing_files:
            raise FileNotFoundError(
                "Missing required frontend assets: "
                + ", ".join(str(path) for path in missing_files)
            )

        return FrontendAssetsResult(
            asset_root=resolved_asset_root,
            checked_files=checked_files,
        )
