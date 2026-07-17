from asgiref.sync import sync_to_async
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from backend.apps.common.response_utils import ResponseUtil
from backend.apps.common.utils.async_api import AsyncAPIView as APIView
from backend.apps.common.utils.async_drf import serializer_data, validate_serializer
from backend.apps.common.utils.pagination_response_mixin import PaginatedResponseMixin
from backend.apps.core_models.constants.common_vo import ResponseVO
from backend.apps.courses.dtos import ReviewCreateDTO, ReviewModerationDTO
from backend.apps.courses.models import Course, CourseCategory, CourseLesson
from backend.apps.courses.repositories.logic import CourseLogicRepository
from backend.apps.courses.serializers import (
    CourseAdminSerializer,
    CourseCategorySerializer,
    CourseDetailSerializer,
    CourseEnrollmentSerializer,
    CourseLessonSerializer,
    CourseListSerializer,
    CourseReviewAdminSerializer,
    CourseReviewCreateSerializer,
    CourseReviewModerationSerializer,
    CourseReviewSerializer,
)
from backend.apps.courses.vo import CourseMessagesVO
from backend.apps.shared.views import BaseViewSet


class PublicCourseViewSet(PaginatedResponseMixin, BaseViewSet):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CourseListSerializer
    tag_name = "Courses"
    exclude_base_query_parameter = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CourseLogicRepository()

    async def list(self, request):
        queryset = await self.logic.list_published_courses_async(
            filters=request.query_params
        )
        return await sync_to_async(
            self.paginated_response,
            thread_sensitive=True,
        )(request, queryset, CourseListSerializer)

    async def retrieve(self, request, pk=None):
        course = await self.logic.get_published_course_async(pk)
        serializer = CourseDetailSerializer(course, context={"request": request})
        return ResponseUtil(
            data=await serializer_data(serializer),
            status_code=ResponseVO.http_200,
        )


class AdminCourseCategoryViewSet(BaseViewSet):
    permission_classes = [IsAdminUser]
    model_class = CourseCategory
    serializer_class = CourseCategorySerializer
    tag_name = "Admin-Course-Categories"
    http_method_names = ["get", "post", "put", "patch", "delete"]


class AdminCourseViewSet(BaseViewSet):
    permission_classes = [IsAdminUser]
    model_class = Course
    serializer_class = CourseAdminSerializer
    tag_name = "Admin-Courses"
    http_method_names = ["get", "post", "put", "patch", "delete"]


class AdminCourseLessonViewSet(BaseViewSet):
    permission_classes = [IsAdminUser]
    model_class = CourseLesson
    serializer_class = CourseLessonSerializer
    tag_name = "Admin-Course-Lessons"
    http_method_names = ["get", "post", "put", "patch", "delete"]


class MyCourseEnrollmentsAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CourseLogicRepository()

    async def get(self, request):
        queryset = await self.logic.list_user_enrollments_async(request.user)
        return await sync_to_async(
            self.paginated_response,
            thread_sensitive=True,
        )(request, queryset, CourseEnrollmentSerializer)


class CourseReviewsAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request and self.request.method == "POST":
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CourseLogicRepository()

    async def get(self, request, course_id):
        queryset = await self.logic.list_approved_reviews_async(course_id)
        return await sync_to_async(
            self.paginated_response,
            thread_sensitive=True,
        )(request, queryset, CourseReviewSerializer)

    async def post(self, request, course_id=None):
        data = {
            **request.data,
            "course_id": course_id or request.data.get("course_id"),
        }
        serializer = CourseReviewCreateSerializer(data=data)
        await validate_serializer(serializer)
        review = await self.logic.submit_review_async(
            user=request.user,
            dto=ReviewCreateDTO(**serializer.validated_data),
        )
        response_serializer = CourseReviewSerializer(
            review,
            context={"request": request},
        )
        return ResponseUtil(
            data={
                "detail": CourseMessagesVO.REVIEW_SUBMITTED,
                "review": await serializer_data(response_serializer),
            },
            status_code=ResponseVO.http_201,
        )


class AdminCourseReviewListAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CourseLogicRepository()

    async def get(self, request):
        queryset = await self.logic.list_reviews_for_admin_async(
            status=request.query_params.get("status")
        )
        return await sync_to_async(
            self.paginated_response,
            thread_sensitive=True,
        )(request, queryset, CourseReviewAdminSerializer)


class AdminCourseReviewModerateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CourseLogicRepository()

    async def patch(self, request, review_id):
        serializer = CourseReviewModerationSerializer(data=request.data)
        await validate_serializer(serializer)
        review = await self.logic.moderate_review_async(
            admin_user=request.user,
            dto=ReviewModerationDTO(
                review_id=review_id,
                **serializer.validated_data,
            ),
        )
        response_serializer = CourseReviewAdminSerializer(
            review,
            context={"request": request},
        )
        return ResponseUtil(
            data={
                "detail": CourseMessagesVO.REVIEW_MODERATED,
                "review": await serializer_data(response_serializer),
            },
            status_code=ResponseVO.http_200,
        )
