from __future__ import annotations

import os
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from django.core.management import call_command, get_commands
from django.test import SimpleTestCase

from backend.apps.common.logic.runtime_config_logic import RuntimeConfigCheckLogic
from backend.apps.core_models.dtos.setup_config import (
    DatabaseConfiguration,
    env_list,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]


class DatabaseEnvironmentFallbackTests(SimpleTestCase):
    def test_blank_sqlite_values_use_safe_defaults(self):
        with mock.patch.dict(
            os.environ,
            {
                "USE_SQL_DATABASE": "true",
                "DATABASE_ENGINE": "",
                "SQLITE_ENGINE": "",
                "SQLITE_NAME": "",
            },
            clear=True,
        ):
            config = DatabaseConfiguration()

        self.assertEqual(config.database_engine, "sqlite")
        self.assertEqual(
            config.sqlite_database_config["ENGINE"],
            "django.db.backends.sqlite3",
        )
        self.assertTrue(
            str(config.sqlite_database_config["NAME"]).endswith(
                "db/db.sqlite3"
            )
        )

    def test_blank_local_list_can_fall_back_to_default(self):
        with mock.patch.dict(os.environ, {"ALLOWED_HOSTS": ""}, clear=True):
            value = env_list(
                "ALLOWED_HOSTS",
                "localhost,127.0.0.1,testserver",
                use_default_if_blank=True,
            )

        self.assertEqual(value, ["localhost", "127.0.0.1", "testserver"])


class RuntimeConfigCheckLogicTests(SimpleTestCase):
    def test_sqlite_parent_is_created_and_configuration_is_valid(self):
        with TemporaryDirectory() as directory:
            database_name = Path(directory) / "nested" / "db.sqlite3"
            settings = SimpleNamespace(
                ENV="local",
                DEBUG=False,
                ALLOWED_HOSTS=["localhost"],
                DATABASES={
                    "default": {
                        "ENGINE": "django.db.backends.sqlite3",
                        "NAME": str(database_name),
                    }
                },
                STATICFILES_DIRS=[PROJECT_ROOT / "backend" / "static"],
                PROMETHEUS_ENABLED=False,
            )

            result = RuntimeConfigCheckLogic().execute(settings)

            self.assertTrue(result.is_valid)
            self.assertTrue(database_name.parent.is_dir())

    def test_dummy_database_has_actionable_error(self):
        settings = SimpleNamespace(
            ENV="local",
            DEBUG=True,
            ALLOWED_HOSTS=[],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.dummy",
                    "NAME": "dummy",
                }
            },
            STATICFILES_DIRS=[PROJECT_ROOT / "backend" / "static"],
            PROMETHEUS_ENABLED=False,
        )

        result = RuntimeConfigCheckLogic().execute(settings)

        self.assertFalse(result.is_valid)
        self.assertIn("USE_SQL_DATABASE=true", " ".join(result.errors))


class StartupCommandTests(SimpleTestCase):
    def test_expected_management_commands_are_registered(self):
        commands = get_commands()

        for command_name in (
            "build_frontend_assets",
            "check_runtime_config",
            "collectstatic",
            "init_project_config",
            "initial_superuser",
        ):
            with self.subTest(command=command_name):
                self.assertIn(command_name, commands)

    def test_build_frontend_assets_validates_runtime_files(self):
        output = StringIO()

        call_command("build_frontend_assets", stdout=output)

        self.assertIn("Frontend assets are ready", output.getvalue())

    def test_runserver_entrypoint_is_fail_fast_and_idempotent(self):
        source = (
            PROJECT_ROOT / "deployment" / "entrypoints" / "runserver.sh"
        ).read_text(encoding="utf-8")

        self.assertIn("set -Eeuo pipefail", source)
        self.assertIn("mkdir -p", source)
        self.assertLess(
            source.index("manage check_runtime_config"),
            source.index("manage migrate --noinput"),
        )
        self.assertNotIn("manage makemigrations", source)
