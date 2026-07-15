from __future__ import annotations

from typing import Any, Type

from django.db.models import QuerySet
from rest_framework.serializers import Serializer

from backend.apps.common.helpers.pagination.http_pagination import HTTPSPageNumberPagination
from backend.apps.common.response_utils import ResponseUtil
from backend.apps.core_models.constants.common_vo import ResponseVO


class PaginatedResponseMixin:
    """Reusable pagination helper for thin API controllers.

    Keeps list endpoints small while preserving the project response shape.
    It intentionally delegates pagination to the existing
    HTTPSPageNumberPagination class used by the shared BaseViewSet logic.
    """

    pagination_class = HTTPSPageNumberPagination

    def paginated_response(
        self,
        request: Any,
        queryset: QuerySet | list,
        serializer_class: Type[Serializer],
        serializer_context: dict[str, Any] | None = None,
    ):
        context = serializer_context or {"request": request}

        if isinstance(queryset, QuerySet) and self._queryset_has_is_deleted(queryset):
            queryset = queryset.filter(is_deleted=False)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer = serializer_class(page, many=True, context=context)
            return paginator.get_paginated_response(serializer.data)

        serializer = serializer_class(queryset, many=True, context=context)
        return ResponseUtil(
            data=serializer.data,
            status_code=ResponseVO.http_200 if serializer.data else ResponseVO.http_204,
        )

    @staticmethod
    def _queryset_has_is_deleted(queryset: QuerySet) -> bool:
        return any(field.name == "is_deleted" for field in queryset.model._meta.fields)
