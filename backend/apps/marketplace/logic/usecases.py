from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from ..enums.status import BookingStatus, ModerationStatus
from ..repositories.marketplace import MarketplaceRepository
from ..value_objects.text import MarketplaceText


class MarketplaceUseCases:
    def __init__(self, repository=None):
        self.repository = repository or MarketplaceRepository()

    def save_profile(self, user, data):
        return self.repository.save_profile(user, data)

    def save_offer(self, user, data):
        mentor = self.repository.get_mentor_for_owner(user)
        if mentor is None:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        return self.repository.create_offer(mentor, data)

    def update_offer(self, user, offer, data):
        if offer.mentor.owner_id != user.pk:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        return self.repository.update_offer(offer, data)

    def save_academy(self, user, data):
        return self.repository.create_academy(user, data)

    def update_academy(self, user, academy, data):
        if academy.owner_id != user.pk:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        return self.repository.update_academy(academy, data)

    def save_opportunity(self, user, academy, data):
        if academy.owner_id != user.pk:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        return self.repository.create_opportunity(academy, data)

    @transaction.atomic
    def add_slot(self, user, offer, starts_at, ends_at):
        if offer.mentor.owner_id != user.pk:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        if starts_at <= timezone.now() or ends_at <= starts_at:
            raise ValidationError(MarketplaceText.INVALID_SLOT)
        self.repository.lock_mentor(offer.mentor_id)
        if self.repository.has_overlapping_slot(offer, starts_at, ends_at):
            raise ValidationError(MarketplaceText.INVALID_SLOT)
        return self.repository.create_slot(offer, starts_at, ends_at)

    @transaction.atomic
    def book(self, user, slot_id):
        slot = self.repository.lock_open_slot(slot_id)
        if not slot or slot.offer.mentor.owner_id == user.pk:
            raise ValidationError(MarketplaceText.NOT_AVAILABLE)
        if self.repository.has_active_booking(slot):
            raise ValidationError(MarketplaceText.NOT_AVAILABLE)
        try:
            with transaction.atomic():
                return self.repository.create_booking(slot, user)
        except IntegrityError as exc:
            raise ValidationError(MarketplaceText.NOT_AVAILABLE) from exc

    @transaction.atomic
    def transition_booking(self, user, booking, action):
        is_mentor = booking.slot.offer.mentor.owner_id == user.pk
        is_student = booking.student_id == user.pk
        transitions = {
            BookingStatus.REQUESTED: {"confirm": (BookingStatus.CONFIRMED, is_mentor), "cancel": (BookingStatus.CANCELLED, is_student or is_mentor)},
            BookingStatus.CONFIRMED: {"complete": (BookingStatus.COMPLETED, is_mentor), "cancel": (BookingStatus.CANCELLED, is_student or is_mentor)},
        }
        state, allowed = transitions.get(booking.status, {}).get(action, (None, False))
        if not allowed or not state:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        locked = self.repository.get_booking(booking.pk, for_update=True)
        if not locked or locked.status != booking.status:
            raise ValidationError(MarketplaceText.NOT_AVAILABLE)
        return self.repository.save_booking_status(locked, state)

    def apply(self, user, opportunity, message, share_resume=False):
        if opportunity.status != ModerationStatus.PUBLISHED or opportunity.academy.status != ModerationStatus.PUBLISHED or opportunity.academy.owner_id == user.pk:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        return self.repository.get_or_create_application(opportunity, user, message, share_resume)

    def revoke_resume_access(self, user, application_id):
        return self.repository.revoke_application_resume(application_id, user)

    def review(self, user, booking, rating, comment):
        if booking.student_id != user.pk or booking.status != BookingStatus.COMPLETED:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        if self.repository.has_review(booking):
            raise ValidationError(MarketplaceText.NOT_AVAILABLE)
        try:
            with transaction.atomic():
                return self.repository.create_review(booking, rating, comment)
        except IntegrityError as exc:
            raise ValidationError(MarketplaceText.NOT_AVAILABLE) from exc

    def add_academy_photo(self, user, academy, image, caption=""):
        if academy.owner_id != user.pk:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        if self.repository.academy_photo_count(academy) >= 12:
            raise ValidationError(MarketplaceText.NOT_AVAILABLE)
        return self.repository.create_photo(academy, image, caption)

    def create_collaboration(self, user, data):
        return self.repository.create_collaboration(user, data)

    @transaction.atomic
    def request_collaboration(self, user, project_id, message):
        project = self.repository.lock_collaboration(project_id)
        if project is None or project.status != ModerationStatus.PUBLISHED or project.owner_id == user.pk:
            raise ValidationError(MarketplaceText.COLLAB_NOT_AVAILABLE)
        if self.repository.existing_collaboration_request(project, user):
            raise ValidationError(MarketplaceText.COLLAB_ALREADY_REQUESTED)
        if self.repository.accepted_collaborator_count(project) + 1 >= project.max_members:
            raise ValidationError(MarketplaceText.COLLAB_NOT_AVAILABLE)
        try:
            with transaction.atomic():
                return self.repository.create_collaboration_request(project, user, message)
        except IntegrityError as exc:
            raise ValidationError(MarketplaceText.COLLAB_ALREADY_REQUESTED) from exc

    @transaction.atomic
    def decide_collaboration_request(self, owner, request_id, decision):
        from ..models import CollaborationRequest
        if decision not in {CollaborationRequest.Status.ACCEPTED, CollaborationRequest.Status.REJECTED}:
            raise ValidationError(MarketplaceText.NOT_AVAILABLE)
        candidate = self.repository.get_collaboration_request(request_id)
        if candidate is None or candidate.project.owner_id != owner.pk:
            raise PermissionDenied(MarketplaceText.NOT_AUTHORIZED)
        # Project -> request is the consistent lock order for concurrent admissions.
        project = self.repository.lock_collaboration(candidate.project_id)
        request = self.repository.lock_collaboration_request(request_id)
        if request is None or request.project_id != project.pk or request.status != CollaborationRequest.Status.PENDING:
            raise ValidationError(MarketplaceText.NOT_AVAILABLE)
        if decision == CollaborationRequest.Status.ACCEPTED and self.repository.accepted_collaborator_count(project) + 1 >= project.max_members:
            raise ValidationError(MarketplaceText.COLLAB_NOT_AVAILABLE)
        return self.repository.save_collaboration_request_status(request, decision)
