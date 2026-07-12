from django.test import TestCase

from dealio.apps.courses.serializers import (
    CourseDetailSerializer,
    CourseReviewCreateSerializer,
)
from dealio.tests.factories import CourseFactory, CourseLessonFactory


class CourseSerializerTests(TestCase):
    def test_detail_serializer_includes_ordered_lessons(self):
        course = CourseFactory.create()
        second = CourseLessonFactory.create(course=course, title="Second", position=2, is_preview=True)
        first = CourseLessonFactory.create(course=course, title="First", position=1, is_preview=True)

        data = CourseDetailSerializer(course).data

        self.assertEqual([item["id"] for item in data["lessons"]], [str(first.id), str(second.id)])

    def test_review_create_serializer_rejects_rating_outside_range(self):
        serializer = CourseReviewCreateSerializer(
            data={
                "course_id": str(CourseFactory.create().id),
                "rating": 6,
                "comment": "Invalid rating",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("rating", serializer.errors)
