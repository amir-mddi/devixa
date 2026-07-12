from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from dealio.apps.common.response_utils import ResponseUtil
from dealio.apps.common.utils.pagination_response_mixin import PaginatedResponseMixin
from dealio.apps.core_models.constants.common_vo import ResponseVO
from dealio.apps.courses.dtos import ReviewCreateDTO, ReviewModerationDTO
from dealio.apps.courses.models import Course, CourseCategory, CourseLesson
from dealio.apps.courses.repositories.logic import CourseLogicRepository
from dealio.apps.courses.serializers import (
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
from dealio.apps.courses.vo import CourseMessagesVO
from dealio.apps.shared.views import BaseViewSet



class PublicCourseViewSet(PaginatedResponseMixin, BaseViewSet):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CourseListSerializer
    tag_name = "Courses"
    exclude_base_query_parameter = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CourseLogicRepository()

    def list(self, request):
        queryset = self.logic.list_published_courses(filters=request.query_params)
        return self.paginated_response(request, queryset, CourseListSerializer)

    def retrieve(self, request, pk=None):
        course = self.logic.get_published_course(pk)
        serializer = CourseDetailSerializer(course, context={"request": request})
        return ResponseUtil(data=serializer.data, status_code=ResponseVO.http_200)


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

    def get(self, request):
        queryset = self.logic.list_user_enrollments(request.user)
        return self.paginated_response(request, queryset, CourseEnrollmentSerializer)


class CourseReviewsAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request and self.request.method == "POST":
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CourseLogicRepository()

    def get(self, request, course_id):
        queryset = self.logic.list_approved_reviews(course_id)
        return self.paginated_response(request, queryset, CourseReviewSerializer)

    def post(self, request, course_id=None):
        data = {**request.data, "course_id": course_id or request.data.get("course_id")}
        serializer = CourseReviewCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        review = self.logic.submit_review(
            user=request.user,
            dto=ReviewCreateDTO(**serializer.validated_data),
        )
        response_serializer = CourseReviewSerializer(review, context={"request": request})
        return ResponseUtil(
            data={
                "detail": CourseMessagesVO.REVIEW_SUBMITTED,
                "review": response_serializer.data,
            },
            status_code=ResponseVO.http_201,
        )


class AdminCourseReviewListAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CourseLogicRepository()

    def get(self, request):
        queryset = self.logic.list_reviews_for_admin(status=request.query_params.get("status"))
        return self.paginated_response(request, queryset, CourseReviewAdminSerializer)


class AdminCourseReviewModerateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CourseLogicRepository()

    def patch(self, request, review_id):
        serializer = CourseReviewModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = self.logic.moderate_review(
            admin_user=request.user,
            dto=ReviewModerationDTO(review_id=review_id, **serializer.validated_data),
        )
        return ResponseUtil(
            data={
                "detail": CourseMessagesVO.REVIEW_MODERATED,
                "review": CourseReviewAdminSerializer(review, context={"request": request}).data,
            },
            status_code=ResponseVO.http_200,
        )
