from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from django.test import SimpleTestCase, TestCase

from dealio.apps.courses.dtos import ReviewModerationDTO
from dealio.apps.courses.entities.course_entities import CoursePriceEntity
from dealio.apps.courses.enums import ReviewStatusEnum
from dealio.apps.courses.repositories.logic import CourseLogicRepository
from dealio.tests.mixins import IsolatedServiceTestMixin


class CourseEntityTests(SimpleTestCase):
    def test_price_entity_reports_free_course(self):
        entity = CoursePriceEntity(course_id=uuid4(), amount=Decimal("0"), currency="irr")

        self.assertTrue(entity.is_free)


class CourseLogicRepositoryTests(IsolatedServiceTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.logic = CourseLogicRepository()
        self.logic.postgres_adapter = MagicMock()

    def test_moderate_review_converts_enum_to_storage_value(self):
        admin = object()
        dto = ReviewModerationDTO(
            review_id=uuid4(),
            status=ReviewStatusEnum.APPROVED,
            admin_note="Looks good",
        )

        self.logic.moderate_review(admin, dto)

        self.logic.postgres_adapter.moderate_review.assert_called_once_with(
            review_id=dto.review_id,
            admin_user=admin,
            status="approved",
            admin_note="Looks good",
        )

    def test_course_level_filters_include_all_supported_levels(self):
        values = {item["value"] for item in self.logic.course_level_filters()}

        self.assertTrue({"all", "beginner", "intermediate", "advanced", "all_levels"}.issubset(values))
