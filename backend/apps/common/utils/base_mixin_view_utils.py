from __future__ import annotations

from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import QuerySet
from rest_framework.exceptions import NotFound

from backend.apps.common.helpers.pagination.http_pagination import HTTPSPageNumberPagination
from backend.apps.common.response_utils import ResponseUtil
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.core_models.constants.common_vo import ResponseVO
from backend.apps.core_models.dtos.base_api_config_dto import BaseAPIConfig
from backend.apps.permissions.access_control import AccessLimitPermission


class BaseLogicControllerUtils:
    """Async application helpers shared by API controllers.

    Query construction stays synchronous because it performs no I/O. Actual ORM
    evaluation uses Django's async QuerySet methods. DRF serializer operations are
    isolated in Django's thread-sensitive executor because serializers may invoke
    synchronous validators, model ``save()``, or relation loading internally.
    """

    @staticmethod
    def validate_uuid(pk: str) -> str:
        try:
            return str(UUID(str(pk)))
        except (ValueError, TypeError) as exc:
            raise NotFound("Invalid UUID") from exc

    @staticmethod
    def apply_owner_permission(config: BaseAPIConfig, queryset: QuerySet) -> QuerySet:
        if AccessLimitPermission.has_access_to_action(config.view, config.request):
            return queryset
        return queryset.filter(user_created_object=config.request.user)

    @staticmethod
    def apply_created_time_filter(request, queryset: QuerySet) -> QuerySet:
        from_timestamp = request.query_params.get("from_created")
        to_timestamp = request.query_params.get("to_created")

        from_date = (
            CommonUtils.convert_timestamp_to_datetime(from_timestamp)
            if from_timestamp
            else None
        )
        to_date = (
            CommonUtils.convert_timestamp_to_datetime(to_timestamp)
            if to_timestamp
            else None
        )

        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)
        return queryset

    @classmethod
    async def get_object(cls, config: BaseAPIConfig, pk: str):
        uuid_val = cls.validate_uuid(pk)
        queryset = config.model_clz.objects.filter(pk=uuid_val, is_deleted=False)
        queryset = await sync_to_async(
            cls.apply_owner_permission,
            thread_sensitive=True,
        )(config, queryset)
        instance = await queryset.afirst()
        if instance is None:
            raise NotFound(f"object with id {pk} not found.")
        return instance

    @staticmethod
    def _paginate_and_serialize(config: BaseAPIConfig, queryset: QuerySet):
        queryset = queryset.filter(is_deleted=False)
        paginator = HTTPSPageNumberPagination()
        page = paginator.paginate_queryset(queryset, config.request, view=config.view)

        if page is not None:
            serializer = config.serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = config.serializer_class(queryset, many=True)
        data = serializer.data
        status_code = ResponseVO.http_200 if data else ResponseVO.http_204
        return ResponseUtil(data=data, status_code=status_code)

    @classmethod
    async def paginate_queryset(cls, config: BaseAPIConfig, queryset: QuerySet):
        return await sync_to_async(
            cls._paginate_and_serialize,
            thread_sensitive=True,
        )(config, queryset)

    @classmethod
    async def list(cls, config: BaseAPIConfig):
        queryset = config.model_clz.objects.all()
        queryset = await sync_to_async(
            cls.apply_owner_permission,
            thread_sensitive=True,
        )(config, queryset)
        queryset = cls.apply_created_time_filter(config.request, queryset)
        return await cls.paginate_queryset(
            config=config,
            queryset=queryset.order_by("-created_at"),
        )

    @classmethod
    async def retrieve(cls, config: BaseAPIConfig, pk=None):
        instance = await cls.get_object(config=config, pk=pk)
        data = await sync_to_async(
            lambda: config.serializer_class(instance).data,
            thread_sensitive=True,
        )()
        return ResponseUtil(data=data, status_code=ResponseVO.http_200)

    @staticmethod
    def _create_sync(config: BaseAPIConfig):
        data = config.request.data
        many = isinstance(data, list)
        serializer = config.serializer_class(
            data=data,
            many=many,
            context={"request": config.request},
        )
        serializer.is_valid(raise_exception=True)

        if many:
            user = (
                config.request.user
                if config.request.user and config.request.user.is_authenticated
                else None
            )
            instances = [
                config.model_clz(
                    **item,
                    user_created_object=user,
                    user_updated_object=user,
                )
                for item in serializer.validated_data
            ]
            config.model_clz.bulk_create_instances(instances)
            response_data = config.serializer_class(instances, many=True).data
        else:
            instance = serializer.save()
            response_data = config.serializer_class(instance).data

        return ResponseUtil(data=response_data, status_code=ResponseVO.http_200)

    @classmethod
    async def create(cls, config: BaseAPIConfig):
        return await sync_to_async(cls._create_sync, thread_sensitive=True)(config)

    @classmethod
    async def update(cls, config: BaseAPIConfig, pk=None):
        instance = await cls.get_object(config=config, pk=pk)

        def update_sync():
            serializer = config.serializer_class(
                instance,
                data=config.request.data,
                partial=True,
                context={
                    "request": config.request,
                    "instance_id": str(instance.id),
                },
            )
            serializer.is_valid(raise_exception=True)
            instance.update_fields(config.request, serializer.validated_data)
            return ResponseUtil(
                data=config.serializer_class(instance).data,
                status_code=ResponseVO.http_200,
            )

        return await sync_to_async(update_sync, thread_sensitive=True)()

    @classmethod
    async def destroy(cls, config: BaseAPIConfig, pk=None):
        instance = await cls.get_object(config=config, pk=pk)
        await sync_to_async(instance.delete, thread_sensitive=True)(soft=True)
        return ResponseUtil(status_code=ResponseVO.http_204)
