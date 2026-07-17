from __future__ import annotations

import ast
from pathlib import Path

from django.test import SimpleTestCase


TELEGRAM_APP_ROOT = Path(__file__).resolve().parents[1]
PERSIAN_CHARACTERS = set(
    "اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیيك"
)


class TelegramTextArchitectureTests(SimpleTestCase):
    orchestration_paths = (
        TELEGRAM_APP_ROOT / "controllers",
        TELEGRAM_APP_ROOT / "logic",
        TELEGRAM_APP_ROOT / "services.py",
    )

    def test_orchestration_layers_do_not_hardcode_persian_user_text(self):
        violations: list[str] = []
        for source_path in self._python_files():
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                    continue
                if not PERSIAN_CHARACTERS.intersection(node.value):
                    continue
                violations.append(f"{source_path.relative_to(TELEGRAM_APP_ROOT)}:{node.lineno}")

        self.assertEqual(
            violations,
            [],
            "Move Telegram user-facing text to a VO/constants module: "
            + ", ".join(violations),
        )

    def _python_files(self):
        for path in self.orchestration_paths:
            if path.is_file():
                yield path
                continue
            yield from path.rglob("*.py")
