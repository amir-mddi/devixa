from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class HTTPSOffsetPagination(LimitOffsetPagination):
    # offset_query_param = 'page_size'
    # limit_query_param = 'page_number'

    def get_paginated_response(self, data):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()
        if next_url:
            next_url = next_url.replace('http://', 'https://')
        if previous_url:
            previous_url = previous_url.replace('http://', 'https://')

        return Response({
            'count': self.count,
            'next': next_url,
            'previous': previous_url,
            'results': data})
