"""Run with: DJANGO_SETTINGS_MODULE=backend.project.test_settings python -m django test backend.apps.marketplace.tests"""
from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from backend.apps.marketplace.enums.status import BookingStatus, ModerationStatus
from backend.apps.marketplace.forms import MentorProfileForm
from backend.apps.marketplace.logic.usecases import MarketplaceUseCases
from backend.apps.marketplace.models import (
    Academy, MentorProfile, MentorReview, MentorshipBooking, MentorshipOffer,
    MentorshipSlot, Opportunity, OpportunityApplication,
)
from backend.tests.factories import UserFactory


class MarketplaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.mentor_owner = UserFactory.create()
        cls.student = UserFactory.create()
        cls.other_student = UserFactory.create()
        cls.academy_owner = UserFactory.create()
        cls.mentor = MentorProfile.objects.create(
            owner=cls.mentor_owner, display_name="Teacher One", headline="Math instructor",
            bio="Experienced mathematics teacher", subjects="Mathematics", city="Tehran",
            status=ModerationStatus.PUBLISHED,
        )
        cls.offer = MentorshipOffer.objects.create(
            mentor=cls.mentor, title="Math class", subject="Mathematics",
            description="One-to-one math class", hourly_price=200000,
            status=ModerationStatus.PUBLISHED,
        )
        cls.academy = Academy.objects.create(
            owner=cls.academy_owner, name="School One", category="School",
            description="Education", programs="Math, Science", city="Tehran",
            address="Central district", status=ModerationStatus.PUBLISHED,
        )
        cls.opportunity = Opportunity.objects.create(
            academy=cls.academy, title="Math teacher needed", subject="Math",
            description="Part-time position", city="Tehran", status=ModerationStatus.PUBLISHED,
        )

    def slot(self):
        return MentorshipSlot.objects.create(
            offer=self.offer, starts_at=timezone.now() + timedelta(days=3),
            ends_at=timezone.now() + timedelta(days=3, hours=1),
        )

    def test_anonymous_can_browse_and_unpublished_entities_are_hidden(self):
        self.assertEqual(self.client.get(reverse("marketplace:mentors")).status_code, 200)
        self.assertContains(self.client.get(reverse("marketplace:academies")), "School One")
        self.assertContains(self.client.get(reverse("marketplace:opportunities")), "Math teacher needed")
        self.offer.status = ModerationStatus.PENDING
        self.offer.save(update_fields=["status"])
        self.assertEqual(self.client.get(reverse("marketplace:offer_detail", args=[self.offer.pk])).status_code, 404)

    def test_profile_edit_requires_login_and_owner_cannot_self_publish(self):
        response = self.client.get(reverse("marketplace:mentor_edit"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.student)
        response = self.client.post(reverse("marketplace:mentor_edit"), {
            "display_name": "New Mentor", "headline": "Science", "bio": "I teach",
            "subjects": "Science", "experience_years": "2", "status": "published",
        })
        self.assertRedirects(response, reverse("marketplace:dashboard"))
        self.assertEqual(MentorProfile.objects.get(owner=self.student).status, ModerationStatus.PENDING)

    def test_resume_is_private_and_rejects_invalid_pdf(self):
        form = MentorProfileForm(data={
            "display_name": "Teacher", "headline": "Math", "bio": "About",
            "subjects": "Math", "experience_years": "1",
        }, files={"resume": SimpleUploadedFile("fake.pdf", b"not-a-real-pdf", content_type="application/pdf")})
        self.assertFalse(form.is_valid())
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("marketplace:resume_download")).status_code, 404)
        self.assertEqual(self.client.get(reverse("marketplace:staff_resume_download", args=[self.mentor.pk])).status_code, 302)

    def test_booking_and_cancellation_unblocks_slot(self):
        slot = self.slot()
        logic = MarketplaceUseCases()
        booking = logic.book(self.student, slot.pk)
        self.assertEqual(booking.status, BookingStatus.REQUESTED)
        with self.assertRaises(ValidationError):
            logic.book(self.other_student, slot.pk)
        with self.assertRaises(PermissionDenied):
            logic.transition_booking(self.other_student, booking, "confirm")
        logic.transition_booking(self.student, booking, "cancel")
        booking2 = logic.book(self.other_student, slot.pk)
        self.assertNotEqual(booking.pk, booking2.pk)

    def test_only_mentor_can_confirm_and_complete_and_student_can_review(self):
        booking = MarketplaceUseCases().book(self.student, self.slot().pk)
        logic = MarketplaceUseCases()
        with self.assertRaises(PermissionDenied):
            logic.transition_booking(self.student, booking, "confirm")
        booking = logic.transition_booking(self.mentor_owner, booking, "confirm")
        booking = logic.transition_booking(self.mentor_owner, booking, "complete")
        with self.assertRaises(PermissionDenied):
            logic.review(self.other_student, booking, 5, "Nice")
        review = logic.review(self.student, booking, 5, "Very helpful")
        self.assertEqual(review.status, ModerationStatus.PENDING)
        with self.assertRaises(ValidationError):
            logic.review(self.student, booking, 5, "Repeated")

    def test_mentor_cannot_book_own_session(self):
        with self.assertRaises(ValidationError):
            MarketplaceUseCases().book(self.mentor_owner, self.slot().pk)

    def test_offer_and_opportunity_ownership(self):
        with self.assertRaises(PermissionDenied):
            MarketplaceUseCases().save_offer(self.student, {
                "title": "Private lesson", "subject": "Math", "description": "Lesson", "hourly_price": 100,
            })
        with self.assertRaises(PermissionDenied):
            MarketplaceUseCases().save_opportunity(self.student, self.academy, {
                "title": "IT support", "subject": "Network", "description": "Service", "city": "Tehran",
            })
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("marketplace:opportunity_new", args=[self.academy.pk])).status_code, 404)

    def test_application_is_unique_and_owner_cannot_apply(self):
        logic = MarketplaceUseCases()
        with self.assertRaises(PermissionDenied):
            logic.apply(self.academy_owner, self.opportunity, "I can help")
        first, created = logic.apply(self.student, self.opportunity, "I can help")
        second, repeated = logic.apply(self.student, self.opportunity, "Again")
        self.assertTrue(created)
        self.assertFalse(repeated)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(OpportunityApplication.objects.filter(opportunity=self.opportunity).count(), 1)

    def test_admin_moderation_not_user_editable(self):
        self.client.force_login(self.mentor_owner)
        response = self.client.post(reverse("marketplace:offer_new"), {
            "title": "New course mentoring", "subject": "Physics", "description": "Teach physics",
            "hourly_price": "200000", "mode": "online", "status": "published",
        })
        self.assertEqual(response.status_code, 302)
        offer = MentorshipOffer.objects.filter(title="New course mentoring").get()
        self.assertEqual(offer.status, ModerationStatus.PENDING)

    def test_unauthorized_book_action_is_forbidden(self):
        booking = MarketplaceUseCases().book(self.student, self.slot().pk)
        self.client.force_login(self.other_student)
        response = self.client.post(reverse("marketplace:booking_action", args=[booking.pk, "confirm"]))
        self.assertEqual(response.status_code, 403)

    def test_homepage_and_mobile_nav_show_marketplace_links(self):
        response = self.client.get(reverse("pages_web:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("marketplace:mentors"))
        self.assertContains(response, reverse("marketplace:academies"))
        self.assertContains(response, reverse("marketplace:opportunities"))

    def test_resume_share_requires_consent_and_can_be_revoked(self):
        logic = MarketplaceUseCases()
        application, _ = logic.apply(self.student, self.opportunity, "Ready to teach", share_resume=True)
        path = reverse("marketplace:application_resume_download", args=[application.pk])
        self.client.force_login(self.other_student)
        self.assertEqual(self.client.get(path).status_code, 404)
        self.client.force_login(self.academy_owner)
        self.assertEqual(self.client.get(path).status_code, 404)  # applicant has no uploaded PDF
        logic.revoke_resume_access(self.student, application.pk)
        application.refresh_from_db()
        self.assertFalse(application.share_resume)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_cannot_revoke_other_applicants_resume_permission(self):
        logic = MarketplaceUseCases()
        application, _ = logic.apply(self.student, self.opportunity, "Hello", share_resume=True)
        self.client.force_login(self.other_student)
        response = self.client.post(reverse("marketplace:revoke_resume_access", args=[application.pk]))
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        self.assertTrue(application.share_resume)

    def test_edit_academy_and_offer_require_ownership_and_reset_moderation(self):
        logic = MarketplaceUseCases()
        with self.assertRaises(PermissionDenied):
            logic.update_academy(self.student, self.academy, {"name": "Fake"})
        with self.assertRaises(PermissionDenied):
            logic.update_offer(self.student, self.offer, {"title": "Fake"})
        logic.update_academy(self.academy_owner, self.academy, {"name": "Updated School"})
        logic.update_offer(self.mentor_owner, self.offer, {"title": "Updated Lesson"})
        self.assertEqual(self.academy.status, ModerationStatus.PENDING)
        self.assertEqual(self.offer.status, ModerationStatus.PENDING)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("marketplace:academy_edit", args=[self.academy.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("marketplace:offer_edit", args=[self.offer.pk])).status_code, 404)
