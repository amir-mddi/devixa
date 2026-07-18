from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from backend.apps.common.dtos.runtime_config_dto import RuntimeConfigCheckDTO


class RuntimeConfigCheckLogic:
    """Validate startup configuration without connecting to external services."""

    SQLITE_ENGINE = "django.db.backends.sqlite3"
    POSTGRES_ENGINE = "django.db.backends.postgresql"
    DUMMY_ENGINE = "django.db.backends.dummy"

    def execute(self, settings: Any) -> RuntimeConfigCheckDTO:
        errors: list[str] = []
        warnings: list[str] = []
        summary: list[str] = []

        default_database = self._get_default_database(settings)
        engine = str(default_database.get("ENGINE") or "").strip()
        name = str(default_database.get("NAME") or "").strip()

        summary.extend(
            (
                f"ENV={getattr(settings, 'ENV', 'unknown')}",
                f"DEBUG={getattr(settings, 'DEBUG', False)}",
                f"DATABASE_ENGINE={engine or '<missing>'}",
                f"DATABASE_NAME={name or '<missing>'}",
            )
        )

        if not engine or engine == self.DUMMY_ENGINE:
            errors.append(
                "A real database is required for migrations. Set "
                "USE_SQL_DATABASE=true and configure DATABASE_ENGINE."
            )
        elif engine == self.SQLITE_ENGINE:
            if not name:
                errors.append("SQLITE_NAME must not be empty.")
            elif name != ":memory:":
                Path(name).expanduser().resolve().parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
        elif engine == self.POSTGRES_ENGINE:
            if not name:
                errors.append("POSTGRES_NAME must be configured for PostgreSQL.")
            if not str(default_database.get("USER") or "").strip():
                errors.append("POSTGRES_USER must be configured for PostgreSQL.")
        else:
            errors.append(f"Unsupported Django database backend: {engine!r}.")

        if not getattr(settings, "DEBUG", False) and not getattr(
            settings,
            "ALLOWED_HOSTS",
            [],
        ):
            errors.append(
                "ALLOWED_HOSTS must contain at least one host when DEBUG=false."
            )

        static_dirs = tuple(getattr(settings, "STATICFILES_DIRS", ()) or ())
        if not static_dirs:
            warnings.append("STATICFILES_DIRS is empty.")
        else:
            missing_static_dirs = [
                str(path)
                for path in static_dirs
                if not Path(path).exists()
            ]
            if missing_static_dirs:
                errors.append(
                    "Missing static source directories: "
                    + ", ".join(missing_static_dirs)
                )

        if getattr(settings, "PROMETHEUS_ENABLED", False):
            multiprocess_dir = str(
                getattr(settings, "PROMETHEUS_MULTIPROC_DIR", "") or ""
            ).strip()
            if multiprocess_dir and not Path(multiprocess_dir).exists():
                warnings.append(
                    "PROMETHEUS_MULTIPROC_DIR does not exist yet; prepare it "
                    "before starting multiple workers."
                )

        return RuntimeConfigCheckDTO(
            errors=tuple(errors),
            warnings=tuple(warnings),
            summary=tuple(summary),
        )

    @staticmethod
    def _get_default_database(settings: Any) -> Mapping[str, Any]:
        databases = getattr(settings, "DATABASES", {}) or {}
        default_database = databases.get("default") or {}
        return default_database
