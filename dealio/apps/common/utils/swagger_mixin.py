from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.views import APIView

from dealio.apps.common.utils.common_utils import CommonUtils
from dealio.apps.shared.serializers import ListResponseSerializer, BaseResponseSerializer


def get_query_params(cls):
    return [
        OpenApiParameter(name="page_number", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                         description="page number"),
        OpenApiParameter(name="page_size", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                         description="page size"),
        OpenApiParameter(name="from_created", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                         description="filter objects created from this timestamp (epoch seconds)"),
        OpenApiParameter(name="to_created", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                         description="filter objects created until this timestamp (epoch seconds)")] if not cls.exclude_base_query_parameter else []


class TaggedSchemaViewSet(viewsets.ViewSet):
    serializer_class = None
    tag_name = None
    list_method_filter_parameters = []
    create_method_filter_parameters = []
    exclude_base_query_parameter = False
    bulk_input = False

    @classmethod
    def as_view(cls, actions=None, **initkwargs):
        view = super().as_view(actions, **initkwargs)
        _query_params = get_query_params(TaggedSchemaViewSet)
        schema_decorator = extend_schema_view(
            list=extend_schema(
                responses={200: ListResponseSerializer(many=True)},
                parameters=_query_params + cls.list_method_filter_parameters,
            ),
            retrieve=extend_schema(responses={200: BaseResponseSerializer}),
            create=extend_schema(
                request=cls.serializer_class(
                    many=True) if (cls.serializer_class and cls.bulk_input) else cls.serializer_class,
                responses={201: BaseResponseSerializer},
                parameters=cls.create_method_filter_parameters,
            ),
            update=extend_schema(
                request=cls.serializer_class(
                    many=True) if (cls.serializer_class and cls.bulk_input) else cls.serializer_class,
                responses={200: BaseResponseSerializer},
                parameters=cls.create_method_filter_parameters,
            ),
            destroy=extend_schema(responses={204: None}),
        )

        return schema_decorator(view)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.tag_name:
            extend_schema(tags=[cls.tag_name])(cls)


class TaggedSchemaAPIView(APIView):
    serializer_class = None
    tag_name = None
    model_class = None

    get_method_filter_parameters = []
    post_method_filter_parameters = []
    put_method_filter_parameters = []
    patch_method_filter_parameters = []
    delete_method_filter_parameters = []

    exclude_base_query_parameter = False
    bulk_input = False

    @classmethod
    def _build_request_serializer(cls, serializer_class):
        if not serializer_class:
            return None

        return serializer_class(many=True) if cls.bulk_input else serializer_class

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)

        _query_params = get_query_params(TaggedSchemaAPIView)

        request_serializer = cls._build_request_serializer(cls.serializer_class)

        # post_schema_serializer_class = CommonUtils.get_serializer_without_fields(
        #     serializer_class=cls.serializer_class,
        #     fields_to_remove=[""],
        # )
        #
        # post_request_serializer = cls._build_request_serializer(
        #     post_schema_serializer_class
        # )

        schema_decorator = extend_schema_view(
            get=extend_schema(
                tags=[cls.tag_name] if cls.tag_name else None,
                responses={
                    200: OpenApiResponse(
                        response=BaseResponseSerializer,
                        description="Object fetched successfully",
                    ),
                    401: OpenApiResponse(description="Unauthorized"),
                    404: OpenApiResponse(description="Object not found"),
                    500: OpenApiResponse(description="Internal server error"),
                },
            ),
            post=extend_schema(
                tags=[cls.tag_name] if cls.tag_name else None,
                request=request_serializer,
                responses={
                    201: OpenApiResponse(
                        response=BaseResponseSerializer,
                        description="Object created successfully",
                    ),
                    400: OpenApiResponse(description="Bad request"),
                    401: OpenApiResponse(description="Unauthorized"),
                    500: OpenApiResponse(description="Internal server error"),
                },
                parameters=cls.post_method_filter_parameters,
            ),
            put=extend_schema(
                tags=[cls.tag_name] if cls.tag_name else None,
                request=request_serializer,
                responses={
                    200: OpenApiResponse(
                        response=BaseResponseSerializer,
                        description="Object updated successfully",
                    ),
                    400: OpenApiResponse(description="Bad request"),
                    401: OpenApiResponse(description="Unauthorized"),
                    404: OpenApiResponse(description="Object not found"),
                    500: OpenApiResponse(description="Internal server error"),
                },
                parameters=cls.put_method_filter_parameters,
            ),
            patch=extend_schema(
                tags=[cls.tag_name] if cls.tag_name else None,
                request=request_serializer,
                responses={
                    200: OpenApiResponse(
                        response=BaseResponseSerializer,
                        description="Object partially updated successfully",
                    ),
                    400: OpenApiResponse(description="Bad request"),
                    401: OpenApiResponse(description="Unauthorized"),
                    404: OpenApiResponse(description="Object not found"),
                    500: OpenApiResponse(description="Internal server error"),
                },
                parameters=cls.patch_method_filter_parameters,
            ),
            delete=extend_schema(
                tags=[cls.tag_name] if cls.tag_name else None,
                responses={
                    204: OpenApiResponse(description="Object deleted successfully"),
                    401: OpenApiResponse(description="Unauthorized"),
                    404: OpenApiResponse(description="Object not found"),
                    500: OpenApiResponse(description="Internal server error"),
                },
                parameters=cls.delete_method_filter_parameters,
            ),
        )

        return schema_decorator(view)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.tag_name:
            extend_schema(tags=[cls.tag_name])(cls)
