from django.db.models import Q
from django.utils import timezone
from ..enums.status import BookingStatus, ModerationStatus
from ..models import Academy, AcademyPhoto, CollaborationProject, CollaborationRequest, MentorProfile, MentorReview, MentorshipBooking, MentorshipOffer, MentorshipSlot, Opportunity, OpportunityApplication


class MarketplaceRepository:
    def public_mentors(self, query="", city=""):
        items = MentorProfile.objects.filter(status=ModerationStatus.PUBLISHED)
        if query:
            items = items.filter(Q(display_name__icontains=query) | Q(subjects__icontains=query) | Q(headline__icontains=query))
        if city:
            items = items.filter(city__icontains=city)
        return items.order_by("-created_at")

    def public_offers(self, subject="", city="", mode="", maximum_price=""):
        items = MentorshipOffer.objects.select_related("mentor").filter(status=ModerationStatus.PUBLISHED, mentor__status=ModerationStatus.PUBLISHED)
        if subject:
            items = items.filter(Q(subject__icontains=subject) | Q(title__icontains=subject))
        if city:
            items = items.filter(Q(city__icontains=city) | Q(mentor__city__icontains=city))
        if mode:
            items = items.filter(mode__in=[mode, "both"])
        if maximum_price and maximum_price.isdigit():
            items = items.filter(hourly_price__lte=int(maximum_price))
        return items.order_by("-created_at")

    def public_academies(self, query="", city=""):
        items = Academy.objects.filter(status=ModerationStatus.PUBLISHED)
        if query:
            items = items.filter(Q(name__icontains=query) | Q(programs__icontains=query) | Q(category__icontains=query))
        if city:
            items = items.filter(city__icontains=city)
        return items.order_by("-created_at")

    def public_opportunities(self, query="", city="", kind=""):
        items = Opportunity.objects.select_related("academy").filter(status=ModerationStatus.PUBLISHED, academy__status=ModerationStatus.PUBLISHED)
        if query:
            items = items.filter(Q(title__icontains=query) | Q(subject__icontains=query))
        if city:
            items = items.filter(city__icontains=city)
        if kind:
            items = items.filter(kind=kind)
        return items.order_by("-created_at")

    def available_slots(self, offer):
        return MentorshipSlot.objects.filter(offer=offer, starts_at__gt=timezone.now()).exclude(bookings__status__in=[BookingStatus.REQUESTED, BookingStatus.CONFIRMED, BookingStatus.COMPLETED]).order_by("starts_at")

    def my_bookings(self, user):
        return MentorshipBooking.objects.select_related("slot__offer__mentor", "student").filter(Q(student=user) | Q(slot__offer__mentor__owner=user)).distinct().order_by("-created_at")

    def get_mentor_for_owner(self, owner):
        return MentorProfile.objects.filter(owner=owner).first()

    def get_public_mentor(self, pk):
        return self.public_mentors().filter(pk=pk).first()

    def get_public_offer(self, pk):
        return self.public_offers().filter(pk=pk).first()

    def get_offer_for_owner(self, pk, owner):
        return MentorshipOffer.objects.select_related("mentor").filter(pk=pk, mentor__owner=owner).first()

    def get_owned_academy(self, pk, owner):
        return Academy.objects.filter(pk=pk, owner=owner).first()

    def get_public_academy(self, pk):
        return self.public_academies().filter(pk=pk).first()

    def get_public_opportunity(self, pk):
        return self.public_opportunities().filter(pk=pk).first()

    def get_booking(self, pk, for_update=False):
        query = MentorshipBooking.objects.select_related("slot__offer__mentor")
        if for_update:
            query = query.select_for_update()
        return query.filter(pk=pk).first()

    def get_completed_student_booking(self, pk, owner):
        return MentorshipBooking.objects.filter(pk=pk, student=owner, status=BookingStatus.COMPLETED).first()

    def profile_offers(self, mentor):
        return self.public_offers().filter(mentor=mentor)

    def public_reviews(self, mentor):
        return MentorReview.objects.filter(booking__slot__offer__mentor=mentor, status=ModerationStatus.PUBLISHED).select_related("booking__student")[:30]

    def academy_opportunities(self, academy):
        return self.public_opportunities().filter(academy=academy)

    def mine_offers(self, user):
        return MentorshipOffer.objects.filter(mentor__owner=user).order_by("-created_at")

    def mine_academies(self, user):
        return Academy.objects.filter(owner=user)

    def academy_applications(self, owner):
        return OpportunityApplication.objects.select_related("opportunity", "applicant").filter(opportunity__academy__owner=owner).order_by("-created_at")[:50]

    def my_applications(self, owner):
        return (
            OpportunityApplication.objects.select_related("opportunity__academy")
            .filter(applicant=owner).order_by("-created_at")[:50]
        )

    def revoke_application_resume(self, application_id, applicant):
        return OpportunityApplication.objects.filter(
            pk=application_id, applicant=applicant, share_resume=True,
        ).update(share_resume=False)

    def save_profile(self, user, data):
        profile, _ = MentorProfile.objects.get_or_create(owner=user, defaults={"display_name": user.get_full_name() or user.username, "headline": "", "bio": "", "subjects": ""})
        for field, value in data.items():
            setattr(profile, field, value)
        profile.status = ModerationStatus.PENDING
        profile.save()
        return profile

    def create_offer(self, mentor, data):
        return MentorshipOffer.objects.create(mentor=mentor, **data)

    def update_offer(self, offer, data):
        for field, value in data.items():
            setattr(offer, field, value)
        offer.status = ModerationStatus.PENDING
        offer.save()
        return offer

    def create_academy(self, user, data):
        return Academy.objects.create(owner=user, **data)

    def update_academy(self, academy, data):
        for field, value in data.items():
            setattr(academy, field, value)
        academy.status = ModerationStatus.PENDING
        academy.save()
        return academy

    def create_opportunity(self, academy, data):
        return Opportunity.objects.create(academy=academy, **data)

    def has_overlapping_slot(self, offer, starts_at, ends_at):
        return MentorshipSlot.objects.filter(offer__mentor_id=offer.mentor_id, starts_at__lt=ends_at, ends_at__gt=starts_at).exists()

    def create_slot(self, offer, starts_at, ends_at):
        return MentorshipSlot.objects.create(offer=offer, starts_at=starts_at, ends_at=ends_at)

    def lock_open_slot(self, slot_id):
        return MentorshipSlot.objects.select_for_update().select_related("offer__mentor").filter(pk=slot_id, offer__status=ModerationStatus.PUBLISHED, offer__mentor__status=ModerationStatus.PUBLISHED, starts_at__gt=timezone.now()).first()

    def has_active_booking(self, slot):
        return MentorshipBooking.objects.filter(slot=slot, status__in=[BookingStatus.REQUESTED, BookingStatus.CONFIRMED, BookingStatus.COMPLETED]).exists()

    def create_booking(self, slot, student):
        return MentorshipBooking.objects.create(slot=slot, student=student)

    def save_booking_status(self, booking, state):
        booking.status = state
        booking.save(update_fields=["status", "updated_at"])
        return booking

    def get_or_create_application(self, opportunity, applicant, message, share_resume=False):
        return OpportunityApplication.objects.get_or_create(
            opportunity=opportunity, applicant=applicant,
            defaults={"message": message, "share_resume": share_resume},
        )

    def authorized_application_resume(self, application_id, academy_owner):
        return (
            OpportunityApplication.objects.select_related("opportunity__academy")
            .filter(pk=application_id, opportunity__academy__owner=academy_owner, share_resume=True)
            .first()
        )

    def has_review(self, booking):
        return MentorReview.objects.filter(booking=booking).exists()

    def create_review(self, booking, rating, comment):
        return MentorReview.objects.create(booking=booking, rating=rating, comment=comment)

    def public_academy_photos(self, academy):
        return AcademyPhoto.objects.filter(academy=academy, status=ModerationStatus.PUBLISHED).order_by("created_at")[:12]

    def academy_photo_count(self, academy):
        return AcademyPhoto.objects.filter(academy=academy).count()

    def create_photo(self, academy, image, caption):
        return AcademyPhoto.objects.create(academy=academy, image=image, caption=caption)

    def get_mentor_for_id(self, pk):
        return MentorProfile.objects.filter(pk=pk).first()

    def public_mentor_for_user(self, user_id):
        return MentorProfile.objects.filter(owner_id=user_id, status=ModerationStatus.PUBLISHED).first()

    def lock_mentor(self, mentor_id):
        return MentorProfile.objects.select_for_update().get(pk=mentor_id)

    def public_collaborations(self, query=""):
        projects = CollaborationProject.objects.select_related("owner").filter(status=ModerationStatus.PUBLISHED)
        if query:
            projects = projects.filter(Q(title__icontains=query) | Q(specialty__icontains=query))
        return projects.order_by("-created_at")

    def get_public_collaboration(self, pk):
        return self.public_collaborations().filter(pk=pk).first()

    def my_collaborations(self, user):
        return CollaborationProject.objects.filter(owner=user).order_by("-created_at")

    def my_collaboration_requests(self, user):
        return CollaborationRequest.objects.select_related("project").filter(applicant=user).order_by("-created_at")

    def collaboration_inbox(self, owner):
        return CollaborationRequest.objects.select_related("project", "applicant").filter(project__owner=owner).order_by("-created_at")

    def create_collaboration(self, owner, data):
        return CollaborationProject.objects.create(owner=owner, **data)

    def lock_collaboration(self, pk):
        return CollaborationProject.objects.select_for_update().filter(pk=pk).first()

    def accepted_collaborator_count(self, project):
        return CollaborationRequest.objects.filter(project=project, status=CollaborationRequest.Status.ACCEPTED).count()

    def existing_collaboration_request(self, project, applicant):
        return CollaborationRequest.objects.filter(project=project, applicant=applicant).first()

    def create_collaboration_request(self, project, applicant, message):
        return CollaborationRequest.objects.create(project=project, applicant=applicant, message=message)

    def get_collaboration_request(self, pk):
        return CollaborationRequest.objects.select_related("project").filter(pk=pk).first()

    def lock_collaboration_request(self, pk):
        return CollaborationRequest.objects.select_for_update().select_related("project").filter(pk=pk).first()

    def save_collaboration_request_status(self, request, status):
        request.status = status
        request.save(update_fields=["status"])
        return request
