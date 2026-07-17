from __future__ import annotations

from asgiref.sync import sync_to_async
from rest_framework.permissions import AllowAny

from backend.apps.articles.logic import ArticleLogic
from backend.apps.articles.serializers import ArticleDetailSerializer, ArticleListSerializer
from backend.apps.common.response_utils import ResponseUtil
from backend.apps.common.utils.async_api import AsyncAPIView as APIView
from backend.apps.common.utils.async_drf import serializer_data
from backend.apps.common.utils.pagination_response_mixin import PaginatedResponseMixin
from backend.apps.core_models.constants.common_vo import ResponseVO


class PublicArticleListAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ArticleListSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = ArticleLogic()

    async def get(self, request):
        # Query construction is lazy and performs no database I/O. DRF's paginator
        # and serializer are synchronous, so only that compatibility section runs
        # in Django's thread-sensitive executor.
        queryset = self.logic.list_public_articles(filters=request.query_params)
        return await sync_to_async(
            self.paginated_response,
            thread_sensitive=True,
        )(request, queryset, self.serializer_class)


class PublicArticleDetailAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ArticleDetailSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = ArticleLogic()

    async def get(self, request, article_id_or_slug):
        detail = await self.logic.get_detail_async(article_id_or_slug)
        serializer = self.serializer_class(
            detail.article,
            context={"request": request},
        )
        return ResponseUtil(
            data=await serializer_data(serializer),
            status_code=ResponseVO.http_200,
        )
