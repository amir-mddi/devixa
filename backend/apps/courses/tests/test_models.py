from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from backend.apps.courses.enums import CourseStatusEnum, ReviewStatusEnum
from backend.apps.courses.models import CourseCategory, CourseLesson
from backend.tests.factories import CourseFactory, ReviewFactory, UserFactory


class CourseModelTests(TestCase):
    def test_category_and_lesson_generate_slugs(self):
        category = CourseCategory.objects.create(title="Python Advanced", slug="")
        course = CourseFactory.create(title="Clean Django", slug="", category=category)
        lesson = CourseLesson.objects.create(course=course, title="Repository Pattern", slug="", position=1)

        self.assertEqual(category.slug, "python-advanced")
        self.assertEqual(course.slug, "clean-django")
        self.assertEqual(lesson.slug, "repository-pattern")

    def test_published_course_sets_published_at_and_reports_state(self):
        course = CourseFactory.create(status=CourseStatusEnum.PUBLISHED.value, published_at=None)

        self.assertTrue(course.is_published)
        self.assertIsNotNone(course.published_at)

    def test_course_is_free_for_zero_or_negative_price(self):
        free_course = CourseFactory.create(price=Decimal("0.00"))

        self.assertTrue(free_course.is_free)

    def test_soft_delete_hides_course_from_is_published_property(self):
        course = CourseFactory.create()

        course.delete()
        course.refresh_from_db()

        self.assertTrue(course.is_deleted)
        self.assertFalse(course.is_published)

    def test_lesson_position_is_unique_inside_course(self):
        course = CourseFactory.create()
        CourseLesson.objects.create(course=course, title="First", slug="first", position=1)

        with self.assertRaises(IntegrityError), transaction.atomic():
            CourseLesson.objects.create(course=course, title="Second", slug="second", position=1)

    def test_review_rating_validation_and_public_state(self):
        review = ReviewFactory.create(rating=6)

        with self.assertRaises(ValidationError):
            review.full_clean()

        review.rating = 5
        review.status = ReviewStatusEnum.APPROVED.value
        review.is_active = True
        review.is_deleted = False
        self.assertTrue(review.is_public)

    def test_user_can_review_course_only_once(self):
        user = UserFactory.create()
        course = CourseFactory.create()
        ReviewFactory.create(user=user, course=course)

        with self.assertRaises(IntegrityError), transaction.atomic():
            ReviewFactory.create(user=user, course=course)
