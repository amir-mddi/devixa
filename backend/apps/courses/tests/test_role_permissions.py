from types import SimpleNamespace
from uuid import uuid4

from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase

from backend.apps.core_models.vo.common_vo import UserRoleVO
from backend.apps.courses.repositories.lms_repository import CourseLMSRepository
from backend.apps.courses.repositories.logic import CourseLogicRepository


def user_with_role(symbol: str, *, user_id=None, is_staff=False, is_superuser=False):
    return SimpleNamespace(
        id=user_id or uuid4(),
        role=SimpleNamespace(symbol=symbol),
        is_authenticated=True,
        is_active=True,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )


class CourseRolePermissionTests(SimpleTestCase):
    def test_assigned_instructor_can_manage_classroom(self):
        instructor = user_with_role(UserRoleVO.INSTRUCTOR)
        course = SimpleNamespace(instructor_id=instructor.id)

        self.assertTrue(CourseLMSRepository.is_instructor(instructor, course))

    def test_unassigned_instructor_cannot_manage_classroom(self):
        instructor = user_with_role(UserRoleVO.INSTRUCTOR)
        course = SimpleNamespace(instructor_id=uuid4())

        self.assertFalse(CourseLMSRepository.is_instructor(instructor, course))

    def test_admin_can_manage_every_classroom(self):
        admin = user_with_role(UserRoleVO.ADMIN)
        course = SimpleNamespace(instructor_id=uuid4())

        self.assertTrue(CourseLMSRepository.is_instructor(admin, course))

    def test_regular_user_cannot_manage_classroom_even_if_assigned(self):
        user = user_with_role(UserRoleVO.USER)
        course = SimpleNamespace(instructor_id=user.id)

        self.assertFalse(CourseLMSRepository.is_instructor(user, course))

    def test_only_admin_role_can_run_admin_course_workflows(self):
        CourseLogicRepository._require_admin(user_with_role(UserRoleVO.ADMIN))
        with self.assertRaises(PermissionDenied):
            CourseLogicRepository._require_admin(user_with_role(UserRoleVO.INSTRUCTOR))
