import json
import os
import time
from datetime import datetime, timedelta

import pytz
from django.core.cache import cache
from django.http import JsonResponse

from dealio.apps.core_models.vo.common_vo import EnvVO, CommonVO
from dealio.apps.shared.repositories.logic import SharedApplicationLogic

ACTIVITY_THRESHOLD = 2
from typing import Any

shared_app_logic = SharedApplicationLogic()


class CommonUtils:
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
        shared_app_logic.expire_an_api_key(expired_key)

    @classmethod
    def fetch_newest_api_key(cls):
        key = shared_app_logic.fetch_newest_api_key()
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
