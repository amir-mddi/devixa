from __future__ import annotations

import hmac

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import Http404, HttpResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    generate_latest,
    multiprocess,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from backend.apps.common.response_utils import ResponseUtil
from backend.apps.common.utils.base_mixin_view_utils import BaseLogicControllerUtils
from backend.apps.common.utils.async_drf import validate_serializer
from backend.apps.common.utils.swagger_mixin import (
    TaggedSchemaAPIView,
    TaggedSchemaViewSet,
)
from backend.apps.core_models.constants.common_vo import ResponseVO
from backend.apps.core_models.dtos.base_api_config_dto import BaseAPIConfig
from backend.apps.shared.models import ApiKeyManagerModel
from backend.apps.shared.repositories.logic import SharedApplicationLogic
from backend.apps.shared.serializers import ApiKeyMngSerializer, ProjectConfigSerializer

EXCEPTION_COUNT = Counter(
    "django_celery_task_total",
    "Total Run Celery Tasks",
    ["method"],
)


class BaseViewSet(TaggedSchemaViewSet):
    serializer_class = None
    model_class = None
    list_method_filter_parameters = []
    tag_name = None
    parameters_field = []

    def get_config(self, request=None):
        return BaseAPIConfig(
            view=self,
            request=request or self.request,
            model_clz=getattr(self, "model_clz", None) or self.model_class,
            serializer_class=self.serializer_class,
        )

    async def get_object(self, pk: str):
        return await BaseLogicControllerUtils.get_object(
            config=self.get_config(),
            pk=pk,
        )

    async def list(self, request):
        return await BaseLogicControllerUtils.list(config=self.get_config(request))

    async def retrieve(self, request, pk=None):
        return await BaseLogicControllerUtils.retrieve(
            config=self.get_config(request),
            pk=pk,
        )

    async def create(self, request):
        return await BaseLogicControllerUtils.create(config=self.get_config(request))

    async def update(self, request, pk=None):
        return await BaseLogicControllerUtils.update(
            config=self.get_config(request),
            pk=pk,
        )

    async def destroy(self, request, pk=None):
        return await BaseLogicControllerUtils.destroy(
            config=self.get_config(request),
            pk=pk,
        )


class ManageMetricsViewSet(BaseViewSet):
    permission_classes = [IsAdminUser]
    model_clz = None
    tag_name = "Shared"
    http_method_names = ["get"]
    serializer_class = None

    async def list(self, request):
        EXCEPTION_COUNT.labels(method="celery_counter").inc()
        return ResponseUtil(status_code=ResponseVO.http_200)


class ApiKeyManagementViewSet(BaseViewSet):
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post"]
    model_clz = ApiKeyManagerModel
    tag_name = "ApiKeyManagement"
    serializer_class = ApiKeyMngSerializer


def _metrics_response(request):
    if request.method != "GET":
        raise Http404

    expected_token = str(
        getattr(settings, "PROMETHEUS_METRICS_TOKEN", "") or ""
    )
    provided_token = request.headers.get("X-Metrics-Token", "")
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        provided_token = authorization.removeprefix("Bearer ").strip()

    if expected_token:
        if not hmac.compare_digest(provided_token, expected_token):
            raise Http404
    elif not settings.DEBUG:
        raise Http404

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    response = HttpResponse(data, content_type=CONTENT_TYPE_LATEST)
    response["Cache-Control"] = "no-store"
    return response


async def prometheus_metrics(request):
    return await sync_to_async(
        _metrics_response,
        thread_sensitive=True,
    )(request)


class ProjectConfigAPIView(TaggedSchemaAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProjectConfigSerializer

    async def get(self, request):
        project_config = await SharedApplicationLogic().get_project_config_async()
        return Response(project_config.as_context() if project_config else {})

    async def patch(self, request):
        return await self._update(request, partial=True)

    async def put(self, request):
        return await self._update(request, partial=False)

    async def _update(self, request, *, partial: bool):
        serializer = self.serializer_class(
            data=request.data,
            partial=partial,
            context={"request": request},
        )
        await validate_serializer(serializer)
        project_config = (
            await SharedApplicationLogic().change_project_config_async(
                data=serializer.validated_data,
                user=request.user,
            )
        )
        return Response(project_config.as_context())


class BaseAPIView(TaggedSchemaAPIView):
    serializer_class = None
    model_class = None

    def get_config(self, request):
        return BaseAPIConfig(
            view=self,
            request=request,
            model_clz=getattr(self, "model_clz", None) or self.model_class,
            serializer_class=self.serializer_class,
        )

    async def get(self, request, pk=None):
        config = self.get_config(request)
        if pk:
            return await BaseLogicControllerUtils.retrieve(config=config, pk=pk)
        return await BaseLogicControllerUtils.list(config=config)

    async def post(self, request):
        return await BaseLogicControllerUtils.create(config=self.get_config(request))

    async def put(self, request, pk=None):
        return await BaseLogicControllerUtils.update(
            config=self.get_config(request),
            pk=pk,
        )

    async def patch(self, request, pk=None):
        return await BaseLogicControllerUtils.update(
            config=self.get_config(request),
            pk=pk,
        )

    async def delete(self, request, pk=None):
        return await BaseLogicControllerUtils.destroy(
            config=self.get_config(request),
            pk=pk,
        )
