from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class HTTPSCursorPagination(CursorPagination):
    page_size = 1
    ordering = '-created_at'
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()

        if self.request.is_secure():
            if next_url:
                next_url = next_url.replace("http://", "https://")
            if previous_url:
                previous_url = previous_url.replace("http://", "https://")

        return Response({
            "next": next_url,
            "previous": previous_url,
            "results": data,
        })
