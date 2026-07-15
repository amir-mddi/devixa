from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from backend.apps.articles.logic import ArticleLogic
from backend.apps.articles.serializers import ArticleDetailSerializer, ArticleListSerializer
from backend.apps.common.response_utils import ResponseUtil
from backend.apps.common.utils.pagination_response_mixin import PaginatedResponseMixin
from backend.apps.core_models.constants.common_vo import ResponseVO


class PublicArticleListAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ArticleListSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = ArticleLogic()

    def get(self, request):
        queryset = self.logic.list_public_articles(filters=request.query_params)
        return self.paginated_response(request, queryset, self.serializer_class)


class PublicArticleDetailAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ArticleDetailSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = ArticleLogic()

    def get(self, request, article_id_or_slug):
        detail = self.logic.get_detail(article_id_or_slug)
        serializer = self.serializer_class(detail.article, context={"request": request})
        return ResponseUtil(data=serializer.data, status_code=ResponseVO.http_200)
