from uuid import UUID

from rest_framework.exceptions import NotFound
from django.db.models import QuerySet

from dealio.apps.common.helpers.pagination.http_pagination import HTTPSPageNumberPagination
from dealio.apps.common.response_utils import ResponseUtil
from dealio.apps.common.utils.common_utils import CommonUtils
from dealio.apps.core_models.constants.common_vo import ResponseVO
from dealio.apps.core_models.dtos.base_api_config_dto import BaseAPIConfig
from dealio.apps.permissions.access_control import AccessLimitPermission


class BaseLogicControllerUtils:

    @staticmethod
    def validate_uuid(pk: str) -> str:
        try:
            return str(UUID(str(pk)))
        except (ValueError, TypeError):
            raise NotFound("Invalid UUID")

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

    @staticmethod
    def get_object(config: BaseAPIConfig, pk: str):
        uuid_val = BaseLogicControllerUtils.validate_uuid(pk)

        queryset = config.model_clz.objects.filter(
            pk=uuid_val,
            is_deleted=False,
        )

        queryset = BaseLogicControllerUtils.apply_owner_permission(
            config=config,
            queryset=queryset,
        )

        instance = queryset.first()

        if instance is None:
            raise NotFound(f"object with id {pk} not found.")

        return instance

    @staticmethod
    def paginate_queryset(config: BaseAPIConfig, queryset: QuerySet):
        queryset = queryset.filter(is_deleted=False)

        paginator = HTTPSPageNumberPagination()
        page = paginator.paginate_queryset(
            queryset,
            config.request,
            view=config.view,
        )

        if page is not None:
            serializer = config.serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = config.serializer_class(queryset, many=True)
        status_code = ResponseVO.http_200 if serializer.data else ResponseVO.http_204

        return ResponseUtil(
            data=serializer.data,
            status_code=status_code,
        )

    @staticmethod
    def list(config: BaseAPIConfig):
        queryset = config.model_clz.objects.all()

        queryset = BaseLogicControllerUtils.apply_owner_permission(
            config=config,
            queryset=queryset,
        )

        queryset = BaseLogicControllerUtils.apply_created_time_filter(
            request=config.request,
            queryset=queryset,
        )

        queryset = queryset.order_by("-created_at")

        return BaseLogicControllerUtils.paginate_queryset(
            config=config,
            queryset=queryset,
        )

    @staticmethod
    def retrieve(config: BaseAPIConfig, pk=None):
        instance = BaseLogicControllerUtils.get_object(
            config=config,
            pk=pk,
        )

        serializer = config.serializer_class(instance)

        return ResponseUtil(
            data=serializer.data,
            status_code=ResponseVO.http_200,
        )

    @staticmethod
    def create(config: BaseAPIConfig):
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

        return ResponseUtil(
            data=response_data,
            status_code=ResponseVO.http_200,
        )

    @staticmethod
    def update(config: BaseAPIConfig, pk=None):
        instance = BaseLogicControllerUtils.get_object(
            config=config,
            pk=pk,
        )

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

    @staticmethod
    def destroy(config: BaseAPIConfig, pk=None):
        instance = BaseLogicControllerUtils.get_object(
            config=config,
            pk=pk,
        )

        instance.delete(soft=True)

        return ResponseUtil(status_code=ResponseVO.http_204)