import logging
from urllib.request import Request
from uuid import UUID
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from prometheus_client import Counter
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest, multiprocess
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from dealio.apps.accounts.serializers import UserSerializer
from dealio.apps.common.helpers.decorators.auth import authentication_required
from dealio.apps.common.helpers.decorators.permission import permission_required
from dealio.apps.common.helpers.decorators.rate_limit import rate_limit
from dealio.apps.common.helpers.decorators.service_action import service_action
from dealio.apps.common.helpers.decorators.validate_http_methods import allowed_methods
from dealio.apps.common.helpers.pagination.http_pagination import HTTPSPageNumberPagination
from dealio.apps.common.response_utils import ResponseUtil
from dealio.apps.common.utils.base_mixin_view_utils import BaseLogicControllerUtils
from dealio.apps.common.utils.common_utils import CommonUtils
from dealio.apps.common.utils.swagger_mixin import TaggedSchemaViewSet, TaggedSchemaAPIView
from dealio.apps.core_models.constants.common_vo import ResponseVO
from dealio.apps.core_models.dtos.base_api_config_dto import BaseAPIConfig
from dealio.apps.permissions.access_control import AccessLimitPermission
from dealio.apps.shared.models import ApiKeyManagerModel
from dealio.apps.shared.serializers import ApiKeyMngSerializer, BaseResponseSerializer

EXCEPTION_COUNT = Counter(
    "django_celery_task_total",
    "Total Run Celery Tasks",
    ["method"]
)

logger = logging.getLogger("dealio")


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

    def get_object(self, pk: str):
        return BaseLogicControllerUtils.get_object(
            config=self.get_config(),
            pk=pk,
        )

    def list(self, request):
        return BaseLogicControllerUtils.list(
            config=self.get_config(request),
        )

    def retrieve(self, request, pk=None):
        return BaseLogicControllerUtils.retrieve(
            config=self.get_config(request),
            pk=pk,
        )

    def create(self, request):
        return BaseLogicControllerUtils.create(
            config=self.get_config(request),
        )

    def update(self, request, pk=None):
        return BaseLogicControllerUtils.update(
            config=self.get_config(request),
            pk=pk,
        )

    def destroy(self, request, pk=None):
        return BaseLogicControllerUtils.destroy(
            config=self.get_config(request),
            pk=pk,
        )


class ManageMetricsViewSet(BaseViewSet):
    permission_classes = [AllowAny]
    model_clz = None
    tag_name = "Shared"
    authentication_classes = []
    http_method_names = ["get"]
    serializer_class = None

    def list(self, request):
        EXCEPTION_COUNT.labels(method="celery_counter").inc()
        return ResponseUtil(status_code=ResponseVO.http_200)


class ApiKeyManagementViewSet(BaseViewSet):
    http_method_names = ["get", "post"]
    model_clz = ApiKeyManagerModel
    tag_name = "ApiKeyManagement"
    serializer_class = ApiKeyMngSerializer


@csrf_exempt
def prometheus_metrics(request):
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)


@method_decorator(service_action(), name="dispatch")
@method_decorator(transaction.atomic, name="dispatch")
# @method_decorator(rate_limit(), name="dispatch")
# @method_decorator(authentication_required(), name="dispatch")
# @method_decorator(permission_required(), name="dispatch")
# @method_decorator(allowed_methods(["*"]), name="dispatch")
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

    def get(self, request, pk=None):
        config = self.get_config(request)

        if pk:
            return BaseLogicControllerUtils.retrieve(
                config=config,
                pk=pk,
            )

        return BaseLogicControllerUtils.list(config=config)

    def post(self, request):
        return BaseLogicControllerUtils.create(
            config=self.get_config(request),
        )

    def put(self, request, pk=None):
        return BaseLogicControllerUtils.update(
            config=self.get_config(request),
            pk=pk,
        )

    def patch(self, request, pk=None):
        return BaseLogicControllerUtils.update(
            config=self.get_config(request),
            pk=pk,
        )

    def delete(self, request, pk=None):
        return BaseLogicControllerUtils.destroy(
            config=self.get_config(request),
            pk=pk,
        )
