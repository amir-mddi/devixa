from unittest.mock import MagicMock

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from backend.apps.shared.dtos.project_config_dto import ProjectConfigDTO
from backend.apps.shared.repositories.adapters.postgres_adapter import PostgresAdapter
from backend.apps.shared.repositories.logic import SharedApplicationLogic
from backend.apps.shared.serializers import ProjectConfigSerializer
from backend.tests.factories import ProjectConfigFactory, UserFactory
from backend.tests.mixins import IsolatedServiceTestMixin


class ProjectConfigTests(IsolatedServiceTestMixin, TestCase):
    def test_dto_from_model_produces_template_context(self):
        config = ProjectConfigFactory.create(display_name="Devixa")

        dto = ProjectConfigDTO.from_model(config)
        context = dto.as_context()

        self.assertEqual(context["display_name"], "Devixa")
        self.assertEqual(context["logo_initial"], "D")

    def test_serializer_normalizes_valid_slug_and_rejects_spaces(self):
        valid = ProjectConfigSerializer(data={"slug": "Devixa_APP"}, partial=True)
        invalid = ProjectConfigSerializer(data={"slug": "invalid slug"}, partial=True)

        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertEqual(valid.validated_data["slug"], "devixa_app")
        self.assertFalse(invalid.is_valid())

    def test_serializer_rejects_private_or_insecure_public_links(self):
        serializer = ProjectConfigSerializer(
            data={"telegram_url": "http://127.0.0.1/internal"},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("telegram_url", serializer.errors)

    def test_postgres_adapter_updates_singleton_instead_of_creating_duplicates(self):
        actor = UserFactory.create()
        first = PostgresAdapter.change_project_config({"name": "First", "slug": "first"}, actor)
        second = PostgresAdapter.change_project_config({"name": "Second"}, actor)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(second.name, "Second")
        self.assertEqual(second.user_updated_object, actor)

    def test_shared_logic_converts_adapter_model_to_dto(self):
        model = ProjectConfigFactory.create()
        logic = SharedApplicationLogic()
        logic.postgres_adapter = MagicMock()
        logic.postgres_adapter.fetch_project_config.return_value = model

        result = logic.get_project_config()

        self.assertIsInstance(result, ProjectConfigDTO)
        self.assertEqual(result.slug, model.slug)
