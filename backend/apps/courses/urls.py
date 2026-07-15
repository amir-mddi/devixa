from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from backend.apps.courses.views import (
    AdminCourseCategoryViewSet,
    AdminCourseLessonViewSet,
    AdminCourseReviewListAPIView,
    AdminCourseReviewModerateAPIView,
    AdminCourseViewSet,
    CourseReviewsAPIView,
    MyCourseEnrollmentsAPIView,
    PublicCourseViewSet,
)

router = routers.DefaultRouter()
router.register(r"courses", PublicCourseViewSet, basename="courses")
router.register(r"admin/categories", AdminCourseCategoryViewSet, basename="admin-course-categories")
router.register(r"admin/courses", AdminCourseViewSet, basename="admin-courses")
router.register(r"admin/lessons", AdminCourseLessonViewSet, basename="admin-course-lessons")

urlpatterns = [
    path("courses/<str:course_id>/reviews/", CourseReviewsAPIView.as_view(), name="course-reviews"),
    path("my/enrollments/", MyCourseEnrollmentsAPIView.as_view(), name="my-course-enrollments"),
    path("admin/reviews/", AdminCourseReviewListAPIView.as_view(), name="admin-course-reviews"),
    path("admin/reviews/<uuid:review_id>/moderate/", AdminCourseReviewModerateAPIView.as_view(), name="admin-course-review-moderate"),
    path("", include(router.urls)),
]
