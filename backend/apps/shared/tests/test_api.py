from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from backend.tests.factories import ProjectConfigFactory, UserFactory


class ProjectConfigAPITests(APITestCase):
    def test_regular_user_cannot_read_project_config_admin_endpoint(self):
        self.client.force_authenticate(UserFactory.create())

        response = self.client.get(reverse("project-config"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_read_and_patch_project_config(self):
        admin = UserFactory.create_admin()
        ProjectConfigFactory.create(name="Before")
        self.client.force_authenticate(admin)

        get_response = self.client.get(reverse("project-config"))
        patch_response = self.client.patch(
            reverse("project-config"),
            {"display_name": "Updated Display"},
            format="json",
        )

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["display_name"], "Updated Display")
