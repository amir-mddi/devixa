from types import SimpleNamespace
from unittest.mock import Mock
from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase
from django.utils.timezone import now
from datetime import timedelta

from backend.apps.courses.logic.lms_logic import CourseLMSLogic


class TopicReleaseTests(SimpleTestCase):
    def setUp(self):
        repository = Mock()
        repository.is_instructor.return_value = False
        repository.has_active_enrollment.return_value = True
        self.logic = CourseLMSLogic(repository)
        self.user = SimpleNamespace(is_authenticated=True)
        self.course = object()

    def test_student_cannot_access_future_section_through_lesson(self):
        section = SimpleNamespace(is_active=True, is_deleted=False, release_at=now() + timedelta(days=1))
        lesson = SimpleNamespace(is_active=True, is_deleted=False, release_at=None, section=section)
        resource = SimpleNamespace(is_active=True, is_deleted=False, release_at=None, section=None, lesson=lesson)
        with self.assertRaises(PermissionDenied):
            self.logic._check_student_content_access(user=self.user, course=self.course, content=resource)

    def test_student_can_access_released_section(self):
        section = SimpleNamespace(is_active=True, is_deleted=False, release_at=now() - timedelta(days=1))
        resource = SimpleNamespace(is_active=True, is_deleted=False, release_at=None, section=section, lesson=None)
        self.logic._check_student_content_access(user=self.user, course=self.course, content=resource)
