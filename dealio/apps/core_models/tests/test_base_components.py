from types import SimpleNamespace

from django.test import RequestFactory, TestCase, SimpleTestCase

from dealio.apps.accounts.models import Access
from dealio.apps.core_models.dtos.base_dto import BaseDTO
from dealio.apps.core_models.enum.base import BaseEnum
from dealio.tests.factories import AccessFactory, UserFactory


class SampleEnum(BaseEnum):
    FIRST = "first"
    SECOND = "second"


class SampleDTO(BaseDTO):
    count: int


class BaseDTOAndEnumTests(SimpleTestCase):
    def test_base_enum_exposes_drf_choices_and_values(self):
        self.assertEqual(SampleEnum.choices(), [("first", "First"), ("second", "Second")])
        self.assertEqual(SampleEnum.values(), ["first", "second"])

    def test_base_dto_ignores_unknown_fields_and_validates_assignment(self):
        dto = SampleDTO(count="2", ignored="value")

        self.assertEqual(dto.count, 2)
        self.assertFalse(hasattr(dto, "ignored"))


class BaseModelTests(TestCase):
    def test_soft_and_hard_delete_behaviors(self):
        soft_deleted = AccessFactory.create()
        hard_deleted = AccessFactory.create()

        soft_deleted.delete()
        hard_deleted.delete(soft=False)

        soft_deleted.refresh_from_db()
        self.assertTrue(soft_deleted.is_deleted)
        self.assertFalse(Access.objects.filter(pk=hard_deleted.pk).exists())

    def test_bulk_create_rejects_mixed_model_types(self):
        with self.assertRaises(TypeError):
            Access.bulk_create_instances([Access(name="valid"), object()])

    def test_update_fields_tracks_actor_and_ignores_unknown_fields(self):
        actor = UserFactory.create()
        access = AccessFactory.create(name="before")
        request = SimpleNamespace(user=actor)

        access.update_fields(request, {"name": "after", "unknown": "ignored"})
        access.refresh_from_db()

        self.assertEqual(access.name, "after")
        self.assertEqual(access.user_updated_object, actor)
        self.assertFalse(hasattr(access, "unknown"))

    def test_to_dict_and_json_serialize_uuid(self):
        access = AccessFactory.create()

        self.assertEqual(access.to_dict()["id"], str(access.id))
        self.assertIn(str(access.id), access.to_json())
