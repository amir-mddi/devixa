from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dealio.apps.courses.enums import ReviewStatusEnum
from dealio.tests.factories import CourseFactory, ReviewFactory, UserFactory


class CourseAPITests(APITestCase):
    def test_public_course_detail_is_available_without_authentication(self):
        course = CourseFactory.create()

        response = self.client.get(reverse("courses-detail", args=[course.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_review_submission_requires_authentication(self):
        course = CourseFactory.create()

        response = self.client.post(
            reverse("course-reviews", args=[course.id]),
            {"rating": 5, "comment": "Great"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("dealio.apps.courses.views.CourseLogicRepository.submit_review")
    def test_authenticated_user_can_submit_review(self, submit_mock):
        user = UserFactory.create()
        course = CourseFactory.create()
        review = ReviewFactory.create(user=user, course=course, status=ReviewStatusEnum.PENDING.value)
        submit_mock.return_value = review
        self.client.force_authenticate(user)

        response = self.client.post(
            reverse("course-reviews", args=[course.id]),
            {"rating": 5, "comment": "Great"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submit_mock.assert_called_once()

    def test_admin_review_list_rejects_regular_user(self):
        self.client.force_authenticate(UserFactory.create())

        response = self.client.get(reverse("admin-course-reviews"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
