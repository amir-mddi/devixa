from __future__ import annotations

import ast
import inspect
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase
from django.utils.module_loading import import_string
from django.urls import URLPattern, URLResolver, get_resolver


APP_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_REQUEST_METHODS = {
    "dispatch",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "create",
    "list",
    "retrieve",
    "update",
    "partial_update",
    "destroy",
}
CONTROLLER_FILE_NAMES = {
    "views.py",
    "controllers.py",
    "controller.py",
}
CONTROLLER_DIRECTORY_NAMES = {"views", "controllers", "web"}


def iter_url_patterns(patterns):
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            yield from iter_url_patterns(pattern.url_patterns)
        elif isinstance(pattern, URLPattern):
            yield pattern


def is_application_callback(callback) -> bool:
    callback_module = getattr(callback, "__module__", "")
    view_class = getattr(callback, "view_class", None)
    viewset_class = getattr(callback, "cls", None)
    class_module = getattr(view_class or viewset_class, "__module__", "")
    return callback_module.startswith("backend.apps.") or class_module.startswith(
        "backend.apps."
    )


def is_controller_file(path: Path) -> bool:
    relative_parts = set(path.relative_to(APP_ROOT).parts[:-1])
    return path.name in CONTROLLER_FILE_NAMES or bool(
        relative_parts & CONTROLLER_DIRECTORY_NAMES
    )


class AsyncControllerArchitectureTests(SimpleTestCase):
    def test_all_application_url_callbacks_are_coroutines(self):
        synchronous_callbacks: list[str] = []

        for pattern in iter_url_patterns(get_resolver().url_patterns):
            callback = pattern.callback
            if not is_application_callback(callback):
                continue
            if not inspect.iscoroutinefunction(callback):
                synchronous_callbacks.append(
                    f"{pattern.pattern}: "
                    f"{getattr(callback, '__module__', '<unknown>')}."
                    f"{getattr(callback, '__name__', callback.__class__.__name__)}"
                )

        self.assertEqual([], synchronous_callbacks)

    def test_no_sync_public_request_handlers_exist_in_application_controllers(self):
        synchronous_handlers: list[str] = []

        for path in APP_ROOT.rglob("*.py"):
            if "migrations" in path.parts or "tests" in path.parts:
                continue
            if not is_controller_file(path):
                continue

            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if not isinstance(node, ast.ClassDef):
                    continue
                for member in node.body:
                    if (
                        isinstance(member, ast.FunctionDef)
                        and member.name in PUBLIC_REQUEST_METHODS
                    ):
                        synchronous_handlers.append(
                            f"{path.relative_to(APP_ROOT)}:{member.lineno} "
                            f"{node.name}.{member.name}"
                        )

        self.assertEqual([], synchronous_handlers)


    def test_all_configured_middleware_are_async_capable(self):
        synchronous_only_middleware = []

        for middleware_path in settings.MIDDLEWARE:
            middleware_class = import_string(middleware_path)
            if not getattr(middleware_class, "async_capable", False):
                synchronous_only_middleware.append(middleware_path)

        self.assertEqual([], synchronous_only_middleware)

    def test_blocking_standard_library_http_client_is_not_used(self):
        violations: list[str] = []

        for path in APP_ROOT.rglob("*.py"):
            if "migrations" in path.parts or "tests" in path.parts:
                continue
            source = path.read_text(encoding="utf-8")
            if "urllib.request" in source or "urlopen(" in source:
                violations.append(str(path.relative_to(APP_ROOT)))

        self.assertEqual([], violations)
