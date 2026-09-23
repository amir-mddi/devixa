from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from backend.apps.marketplace.logic.usecases import MarketplaceUseCases
from backend.apps.marketplace.models import CollaborationProject, CollaborationRequest
from backend.tests.factories import UserFactory


class CollaborationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = UserFactory.create()
        cls.applicant = UserFactory.create()
        cls.other = UserFactory.create()
        cls.project = CollaborationProject.objects.create(
            owner=cls.owner,
            title="Educational collaboration",
            specialty="Python",
            description="Build a course together",
            max_members=2,
        )

    def test_unpublished_projects_hidden_from_public(self):
        self.assertNotContains(self.client.get(reverse("marketplace:collaborations")), self.project.title)
        self.assertEqual(self.client.get(reverse("marketplace:collaboration_detail", args=[self.project.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("marketplace:collaboration_apply", args=[self.project.pk])).status_code, 302)
        self.client.force_login(self.applicant)
        self.assertEqual(self.client.get(reverse("marketplace:collaboration_apply", args=[self.project.pk])).status_code, 404)

    def test_create_requires_login_and_moderation(self):
        self.assertEqual(self.client.get(reverse("marketplace:collaboration_new")).status_code, 302)
        self.client.force_login(self.owner)
        response = self.client.post(reverse("marketplace:collaboration_new"), {
            "title": "Course teamwork", "specialty": "Django",
            "description": "Collaborate on course material", "mode": "online", "max_members": "3",
            "status": "published", "owner": self.other.pk,
        })
        self.assertEqual(response.status_code, 302)
        item = CollaborationProject.objects.get(title="Course teamwork")
        self.assertEqual(item.owner_id, self.owner.pk)
        self.assertEqual(item.status, "pending")

    def test_join_owner_permission_duplicate_and_capacity(self):
        self.project.status = "published"
        self.project.save(update_fields=["status"])
        logic = MarketplaceUseCases()
        with self.assertRaises(ValidationError):
            logic.request_collaboration(self.owner, self.project.pk, "own project")
        self.client.force_login(self.applicant)
        response = self.client.post(reverse("marketplace:collaboration_apply", args=[self.project.pk]), {"message": "I can help"})
        self.assertEqual(response.status_code, 302)
        request = CollaborationRequest.objects.get(project=self.project, applicant=self.applicant)
        with self.assertRaises(ValidationError):
            logic.request_collaboration(self.applicant, self.project.pk, "duplicate")
        with self.assertRaises(PermissionDenied):
            logic.decide_collaboration_request(self.other, request.pk, "accepted")
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("marketplace:collaboration_decide", args=[request.pk, "accepted"])).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("marketplace:collaboration_decide", args=[request.pk, "accepted"])).status_code, 405)
        self.assertEqual(self.client.post(reverse("marketplace:collaboration_decide", args=[request.pk, "accepted"])).status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, "accepted")
        with self.assertRaises(ValidationError):
            logic.request_collaboration(self.other, self.project.pk, "too late")
        with self.assertRaises(ValidationError):
            logic.decide_collaboration_request(self.owner, request.pk, "accepted")

    def test_dashboard_shows_only_owned_and_sent_requests(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("marketplace:dashboard"))
        self.assertContains(response, self.project.title)
        self.client.force_login(self.other)
        response = self.client.get(reverse("marketplace:dashboard"))
        self.assertNotContains(response, self.project.title)
