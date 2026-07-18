from __future__ import annotations

from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from backend.apps.common.utils.base_mixin_view_utils import BaseLogicControllerUtils
from backend.apps.common.utils.async_drf import validate_serializer
from backend.apps.common.utils.swagger_mixin import (
    TaggedSchemaAPIView,
    TaggedSchemaViewSet,
)
from backend.apps.core_models.dtos.base_api_config_dto import BaseAPIConfig
from backend.apps.shared.models import ApiKeyManagerModel
from backend.apps.shared.repositories.logic import SharedApplicationLogic
from backend.apps.shared.serializers import ApiKeyMngSerializer, ProjectConfigSerializer


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


class ApiKeyManagementViewSet(BaseViewSet):
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post"]
    model_clz = ApiKeyManagerModel
    tag_name = "ApiKeyManagement"
    serializer_class = ApiKeyMngSerializer


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
