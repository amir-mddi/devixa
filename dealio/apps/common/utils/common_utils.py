import json
import logging
import os
import time
from datetime import datetime, timedelta

import pytz
from django.core.cache import cache
from django.http import JsonResponse

from dealio.apps.core_models.vo.common_vo import EnvVO, CommonVO
ACTIVITY_THRESHOLD = 2
from typing import Any


class CommonUtils:
    @classmethod
    def get_project_logger_name(cls) -> str:
        try:
            from django.conf import settings

            configured_logger_name = getattr(settings, "PROJECT_LOGGER_NAME", None)
        except Exception:
            configured_logger_name = None

        logger_name = (
            configured_logger_name
            or os.environ.get("PROJECT_LOGGER_NAME")
            or os.environ.get("PROJECT_SLUG")
            or os.environ.get("PROJECT_NAME")
            or "project"
        )

        return str(logger_name).strip().lower().replace(" ", "-")

    @classmethod
    def get_project_logger(cls, module_name: str | None = None) -> logging.Logger:
        logger_name = cls.get_project_logger_name()
        normalized_module_name = str(module_name or "").strip(".")

        if not normalized_module_name:
            return logging.getLogger(logger_name)

        return logging.getLogger(f"{logger_name}.{normalized_module_name}")


    @classmethod
    def normalize_path_part(cls, value: str | None) -> str:
        cleaned_value = str(value or "").strip().replace("\\", "/")
        cleaned_value = cleaned_value.strip("/")

        if cleaned_value.startswith("static/"):
            cleaned_value = cleaned_value.removeprefix("static/").strip("/")

        return cleaned_value

    @classmethod
    def get_static_asset_root(cls) -> str:
        try:
            from django.conf import settings

            configured_asset_root = getattr(settings, "PROJECT_STATIC_ASSET_ROOT", None)
        except Exception:
            configured_asset_root = None

        return cls.normalize_path_part(
            configured_asset_root
            or os.environ.get("PROJECT_STATIC_ASSET_ROOT")
            or "app/assets"
        )

    @classmethod
    def build_project_static_path(cls, path: str | None) -> str:
        asset_root = cls.get_static_asset_root()
        cleaned_path = cls.normalize_path_part(path)

        if not cleaned_path:
            return asset_root

        if cleaned_path == asset_root or cleaned_path.startswith(f"{asset_root}/"):
            return cleaned_path

        return f"{asset_root}/{cleaned_path}" if asset_root else cleaned_path

    @classmethod
    def should_serve_static_files(cls) -> bool:
        try:
            from django.conf import settings

            return bool(
                getattr(settings, "DEBUG", False)
                or getattr(settings, "PROJECT_SERVE_STATIC_FILES", False)
            )
        except Exception:
            return bool(os.environ.get("PROJECT_SERVE_STATIC_FILES", "").lower() in {"1", "true", "yes", "on"})

    @classmethod
    def get_first_staticfiles_dir(cls):
        from django.conf import settings

        static_dirs = list(getattr(settings, "STATICFILES_DIRS", []) or [])
        if static_dirs:
            return static_dirs[0]

        return getattr(settings, "STATIC_ROOT", None)

    @classmethod
    def get_serializer_without_fields(cls, serializer_class, fields_to_remove):
        if not serializer_class:
            return None

        class SchemaSerializer(serializer_class):
            class Meta(serializer_class.Meta):
                pass

        fields_to_remove = set(fields_to_remove)

        SchemaSerializer.Meta.fields = tuple(
            field
            for field in serializer_class.Meta.fields
            if field not in fields_to_remove
        )

        SchemaSerializer.Meta.read_only_fields = tuple(
            field
            for field in getattr(serializer_class.Meta, "read_only_fields", ())
            if field not in fields_to_remove
        )

        removed_fields_name = "".join(
            field.title().replace("_", "")
            for field in fields_to_remove
        )

        SchemaSerializer.__name__ = (
            f"{serializer_class.__name__}Without{removed_fields_name}"
        )
        SchemaSerializer.__qualname__ = SchemaSerializer.__name__

        return SchemaSerializer

    @staticmethod
    def is_authenticated_request(request):
        if request is None:
            return False

        user = getattr(request, "user", None)
        return user is not None and user.is_authenticated

    @staticmethod
    def get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")

    @staticmethod
    def get_request_from_args_kwargs(*args, **kwargs):
        request = kwargs.get("request")

        if request is not None:
            return request

        for arg in args:
            if hasattr(arg, "META") and hasattr(arg, "method"):
                return arg

        return None

    @staticmethod
    def update_user_activity(user_id):
        current_time = str(time.time())
        cache.set(f"user_last_activity_with_id:{user_id}", current_time, timeout=timedelta(hours=24))

    @staticmethod
    def get_active_users(request):
        active_users = []
        current_time = time.time()
        all_users = cache.get("all_users")

        if all_users:
            for user_id in all_users:
                last_activity_str = cache.get(f"user_last_activity_with_id:{user_id}")
                if last_activity_str:
                    last_activity_time = float(last_activity_str)
                    if current_time - last_activity_time <= ACTIVITY_THRESHOLD * 60:
                        active_users.append(user_id)

        return JsonResponse({'active_users': active_users})

    @staticmethod
    def add_user_to_cache(user_id):
        all_users = cache.get("all_users", set())
        all_users.add(user_id)
        cache.set("all_users", all_users, timeout=timedelta(hours=24))

    @classmethod
    def ensure_init_created(cls, base_dir: str) -> None:
        for root, dirs, files in os.walk(base_dir):
            if "__init__.py" not in files and all(
                    not dir in root for dir in CommonVO.dirs_skip_creation_init
            ):
                init_path = os.path.join(root, "__init__.py")
                open(init_path, "w").close()

    @classmethod
    def convert_binary_to_str(cls, content: bytes) -> str:
        string_content = content.decode("utf-8")
        return string_content

    @classmethod
    def convert_py_object_to_dict(cls, data):
        return [item.to_dict() if hasattr(item, "to_dict") else item for item in data]

    @classmethod
    def is_local_env(cls) -> bool:
        return os.environ.get("ENV", EnvVO.local) == EnvVO.local

    @classmethod
    def is_prod_env(cls) -> bool:
        return os.environ.get("ENV", EnvVO.production) == EnvVO.production

    @classmethod
    def is_dev_env(cls) -> bool:
        return os.environ.get("ENV", EnvVO.development) == EnvVO.development

    @classmethod
    def convert_timestamp_to_datetime(cls, time):
        try:
            date = datetime.fromtimestamp(time, tz=pytz.utc)
        except Exception as e:
            print(f"First attempt error: {e}")

            try:
                time_set = int(time) / 1000
                date = datetime.fromtimestamp(time_set, tz=pytz.utc)
            except Exception as e:
                print(f"Second attempt error: {e}")
        return date if time else None

    @classmethod
    def to_human_text(cls, s: str) -> str:
        try:
            v = json.loads(s)
            if isinstance(v, str):
                return v
        except json.JSONDecodeError:
            pass
        try:
            return s.encode("utf-8").decode("unicode_escape")
        except Exception:
            return s

    @classmethod
    def expire_an_api_key(cls, expired_key):
        from dealio.apps.shared.repositories.logic import SharedApplicationLogic

        SharedApplicationLogic().expire_an_api_key(expired_key)

    @classmethod
    def fetch_newest_api_key(cls):
        from dealio.apps.shared.repositories.logic import SharedApplicationLogic

        key = SharedApplicationLogic().fetch_newest_api_key()
        return key


class PayloadNormalizer:
    @staticmethod
    def convert_binary_to_str(value: Any) -> str:
        if isinstance(value, (bytearray, memoryview)):
            value = bytes(value)
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, str):
            return value
        return value

    @classmethod
    def _decode_key(cls, key: Any) -> Any:
        if isinstance(key, (bytes, bytearray, memoryview)):
            return cls.convert_binary_to_str(key)
        return key

    @classmethod
    def decode_messages_of_response(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                cls._decode_key(k): cls.decode_messages_of_response(v)
                for k, v in obj.items()
            }

        if isinstance(obj, list):
            return [cls.decode_messages_of_response(v) for v in obj]

        if isinstance(obj, tuple):
            return tuple(cls.decode_messages_of_response(v) for v in obj)

        if isinstance(obj, set):
            return {cls.decode_messages_of_response(v) for v in obj}

        if isinstance(obj, (bytes, bytearray, memoryview)):
            return cls.convert_binary_to_str(obj)

        if isinstance(obj, str):
            return obj

        return obj
