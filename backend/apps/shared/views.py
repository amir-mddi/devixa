from uuid import UUID
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from prometheus_client import Counter
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAdminUser
from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest, multiprocess
from django.conf import settings
from django.http import Http404, HttpResponse
import hmac
from rest_framework.views import APIView
from rest_framework.response import Response

from backend.apps.accounts.serializers import UserSerializer
from backend.apps.common.helpers.decorators.auth import authentication_required
from backend.apps.common.helpers.decorators.permission import permission_required
from backend.apps.common.helpers.decorators.rate_limit import rate_limit
from backend.apps.common.helpers.decorators.service_action import service_action
from backend.apps.common.helpers.decorators.validate_http_methods import allowed_methods
from backend.apps.common.helpers.pagination.http_pagination import HTTPSPageNumberPagination
from backend.apps.common.response_utils import ResponseUtil
from backend.apps.common.utils.base_mixin_view_utils import BaseLogicControllerUtils
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.common.utils.swagger_mixin import TaggedSchemaViewSet, TaggedSchemaAPIView
from backend.apps.core_models.constants.common_vo import ResponseVO
from backend.apps.core_models.dtos.base_api_config_dto import BaseAPIConfig
from backend.apps.permissions.access_control import AccessLimitPermission
from backend.apps.shared.repositories.logic import SharedApplicationLogic
from backend.apps.shared.models import ApiKeyManagerModel
from backend.apps.shared.serializers import ApiKeyMngSerializer, BaseResponseSerializer, ProjectConfigSerializer

EXCEPTION_COUNT = Counter(
    "django_celery_task_total",
    "Total Run Celery Tasks",
    ["method"]
)

logger = CommonUtils.get_project_logger(__name__)


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
    permission_classes = [IsAdminUser]
    model_clz = None
    tag_name = "Shared"
    http_method_names = ["get"]
    serializer_class = None

    def list(self, request):
        EXCEPTION_COUNT.labels(method="celery_counter").inc()
        return ResponseUtil(status_code=ResponseVO.http_200)


class ApiKeyManagementViewSet(BaseViewSet):
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post"]
    model_clz = ApiKeyManagerModel
    tag_name = "ApiKeyManagement"
    serializer_class = ApiKeyMngSerializer


def prometheus_metrics(request):
    if request.method != "GET":
        raise Http404

    expected_token = str(getattr(settings, "PROMETHEUS_METRICS_TOKEN", "") or "")
    provided_token = request.headers.get("X-Metrics-Token", "")
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        provided_token = authorization.removeprefix("Bearer ").strip()

    if expected_token:
        if not hmac.compare_digest(provided_token, expected_token):
            raise Http404
    elif not settings.DEBUG:
        # Metrics are disabled by default outside development unless protected.
        raise Http404

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    response = HttpResponse(data, content_type=CONTENT_TYPE_LATEST)
    response["Cache-Control"] = "no-store"
    return response




class ProjectConfigAPIView(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProjectConfigSerializer

    def get(self, request):
        project_config = SharedApplicationLogic().get_project_config()
        return Response(project_config.as_context() if project_config else {})

    def patch(self, request):
        serializer = self.serializer_class(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        project_config = SharedApplicationLogic().change_project_config(
            data=serializer.validated_data,
            user=request.user,
        )
        return Response(project_config.as_context())

    def put(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        project_config = SharedApplicationLogic().change_project_config(
            data=serializer.validated_data,
            user=request.user,
        )
        return Response(project_config.as_context())

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
