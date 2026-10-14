from unittest.mock import Mock
from django.test import SimpleTestCase
from backend.apps.software_services.dtos.request_dto import CreateSoftwareRequestDTO
from backend.apps.software_services.forms import SoftwareProjectRequestForm
from backend.apps.software_services.logic.request_logic import CreateSoftwareRequestLogic
from backend.apps.software_services.enums.request_enums import (
    ServiceCategory, ProjectBudget, ProjectTimeline,
)


def valid_payload():
    return dict(full_name="سارا احمدی", email="Sara@EXAMPLE.com", phone="09123456789",
                category=ServiceCategory.WEBSITE, project_title="سایت شرکتی", description="طراحی سایت حرفه‌ای برای کسب‌وکار جدیدمان",
                budget=ProjectBudget.UNDECIDED, timeline=ProjectTimeline.FLEXIBLE, reference_url="")


class SoftwareRequestLogicTests(SimpleTestCase):
    def test_workflow_does_not_need_database(self):
        repository = Mock()
        repository.create.return_value = object()
        dto = CreateSoftwareRequestDTO(**valid_payload())
        result = CreateSoftwareRequestLogic(repository).execute(dto=dto)
        self.assertIs(result, repository.create.return_value)
        saved = repository.create.call_args.kwargs["dto"]
        self.assertEqual(saved.email, "sara@example.com")

    def test_invalid_phone_and_honeypot(self):
        form = SoftwareProjectRequestForm({**valid_payload(), "phone": "<script>"})
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)
        form = SoftwareProjectRequestForm({**valid_payload(), "website": "spam.example"})
        self.assertFalse(form.is_valid())
        self.assertIn("website", form.errors)

    def test_valid_form(self):
        form = SoftwareProjectRequestForm(valid_payload())
        self.assertTrue(form.is_valid(), form.errors)
