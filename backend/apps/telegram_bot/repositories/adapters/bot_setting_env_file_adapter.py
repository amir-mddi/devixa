from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Mapping

from django.conf import settings
from django.core.exceptions import ValidationError


class BotSettingEnvFileAdapter:
    """Safe writer for allow-listed bot settings in the active deployment env file.

    This adapter intentionally does not expose arbitrary environment variables.
    The service layer passes only env names that exist in BotSettingRegistryVO.
    """

    _ASSIGNMENT_RE = re.compile(r"^(?P<prefix>\s*(?:export\s+)?)(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=")
    _SIMPLE_VALUE_RE = re.compile(r"^[A-Za-z0-9_./:@+\-=,]+$")

    @classmethod
    def env_file_path(cls) -> Path:
        configured_path = getattr(settings, "BOT_RUNTIME_ENV_FILE_PATH", "") or os.environ.get("BOT_RUNTIME_ENV_FILE_PATH", "")
        if configured_path:
            return Path(configured_path).expanduser().resolve()

        base_dir = Path(getattr(settings, "BASE_DIR", Path.cwd())).resolve()
        environment_name = os.environ.get("ENV", "local") or "local"
        return (base_dir / "deployment" / "env" / f"{environment_name}.env").resolve()

    @classmethod
    def is_write_enabled(cls) -> bool:
        raw_value = os.environ.get(
            "BOT_RUNTIME_ENV_WRITE_ENABLED",
            str(getattr(settings, "BOT_RUNTIME_ENV_WRITE_ENABLED", "true")),
        )
        return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}

    @classmethod
    def update_values(cls, values_by_env_name: Mapping[str, str]) -> Path:
        if not cls.is_write_enabled():
            raise ValidationError("Writing bot settings to env file is disabled.")

        env_file_path = cls.env_file_path()
        cls._ensure_allowed_path(env_file_path)
        env_file_path.parent.mkdir(parents=True, exist_ok=True)

        lines = env_file_path.read_text(encoding="utf-8").splitlines(keepends=True) if env_file_path.exists() else []
        remaining_values = {key: str(value or "") for key, value in values_by_env_name.items()}
        output_lines: list[str] = []
        touched_keys: set[str] = set()

        for line in lines:
            match = cls._ASSIGNMENT_RE.match(line)
            if not match:
                output_lines.append(line)
                continue

            key = match.group("key")
            if key not in remaining_values:
                output_lines.append(line)
                continue

            # Update the first active assignment for each key and remove later duplicates.
            if key in touched_keys:
                continue

            prefix = match.group("prefix") or ""
            output_lines.append(f"{prefix}{key}={cls._format_env_value(remaining_values[key])}\n")
            touched_keys.add(key)

        missing_keys = [key for key in remaining_values.keys() if key not in touched_keys]
        if missing_keys:
            if output_lines and not output_lines[-1].endswith("\n"):
                output_lines[-1] = f"{output_lines[-1]}\n"
            if output_lines and output_lines[-1].strip():
                output_lines.append("\n")
            output_lines.append("# Bot runtime settings managed from admin panel\n")
            for key in missing_keys:
                output_lines.append(f"{key}={cls._format_env_value(remaining_values[key])}\n")

        temp_path = env_file_path.with_suffix(f"{env_file_path.suffix}.tmp")
        temp_path.write_text("".join(output_lines), encoding="utf-8")
        temp_path.replace(env_file_path)

        for key, value in remaining_values.items():
            os.environ[key] = value

        return env_file_path

    @classmethod
    def _ensure_allowed_path(cls, env_file_path: Path) -> None:
        base_dir = Path(getattr(settings, "BASE_DIR", Path.cwd())).resolve()
        default_env_dir = (base_dir / "deployment" / "env").resolve()
        allow_any_path = str(
            os.environ.get(
                "BOT_RUNTIME_ENV_WRITE_ALLOW_ANY_PATH",
                getattr(settings, "BOT_RUNTIME_ENV_WRITE_ALLOW_ANY_PATH", "false"),
            )
        ).strip().lower() in {"1", "true", "yes", "on"}

        if allow_any_path:
            return

        try:
            env_file_path.relative_to(default_env_dir)
        except ValueError as exc:
            raise ValidationError(
                "Refusing to write outside deployment/env. Set BOT_RUNTIME_ENV_WRITE_ALLOW_ANY_PATH=true if you really need it."
            ) from exc

    @classmethod
    def _format_env_value(cls, value: str) -> str:
        value = str(value or "")
        if value == "":
            return '""'
        if cls._SIMPLE_VALUE_RE.match(value):
            return value
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
