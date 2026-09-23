import uuid
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from .adapters.private_storage import resume_storage
from .enums.status import BookingStatus, DeliveryMode, ModerationStatus, OpportunityKind


def resume_upload_to(instance, filename):
    return f"mentor_resumes/{instance.owner_id}/{uuid.uuid4().hex}.pdf"


class MentorProfile(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="mentor_profile", on_delete=models.CASCADE)
    display_name = models.CharField(max_length=140)
    headline = models.CharField(max_length=200)
    bio = models.TextField()
    subjects = models.CharField(max_length=250, help_text="موضوعات تدریس، جداشده با ویرگول")
    experience_years = models.PositiveSmallIntegerField(default=0)
    city = models.CharField(max_length=100, blank=True)
    portfolio_url = models.URLField(blank=True)
    resume = models.FileField(storage=resume_storage, upload_to=resume_upload_to, blank=True)
    status = models.CharField(max_length=12, choices=ModerationStatus.choices, default=ModerationStatus.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name


class MentorshipOffer(models.Model):
    mentor = models.ForeignKey(MentorProfile, related_name="offers", on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    subject = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    hourly_price = models.DecimalField(max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    city = models.CharField(max_length=100, blank=True)
    mode = models.CharField(max_length=10, choices=DeliveryMode.choices, default=DeliveryMode.ONLINE)
    status = models.CharField(max_length=12, choices=ModerationStatus.choices, default=ModerationStatus.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MentorshipSlot(models.Model):
    offer = models.ForeignKey(MentorshipOffer, related_name="slots", on_delete=models.CASCADE)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["offer", "starts_at"], name="marketplace_unique_offer_slot")]
        ordering = ["starts_at"]

    def __str__(self):
        return f"{self.offer_id}: {self.starts_at}"


class MentorshipBooking(models.Model):
    slot = models.ForeignKey(MentorshipSlot, related_name="bookings", on_delete=models.PROTECT)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="mentorship_bookings", on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=BookingStatus.choices, default=BookingStatus.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["slot"], condition=Q(status__in=["requested", "confirmed", "completed"]), name="marketplace_one_active_booking_per_slot")]


class MentorReview(models.Model):
    booking = models.OneToOneField(MentorshipBooking, related_name="review", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=2000)
    status = models.CharField(max_length=12, choices=ModerationStatus.choices, default=ModerationStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)


class Academy(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="owned_academies", on_delete=models.PROTECT)
    name = models.CharField(max_length=180)
    category = models.CharField(max_length=100, help_text="مدرسه، هنرستان، آموزشگاه یا سایر")
    description = models.TextField()
    programs = models.TextField(help_text="رشته‌ها و دوره‌های ارائه‌شده")
    facilities = models.TextField(blank=True)
    city = models.CharField(max_length=100, db_index=True)
    address = models.CharField(max_length=300)
    website = models.URLField(blank=True)
    public_phone = models.CharField(max_length=25, blank=True)
    status = models.CharField(max_length=12, choices=ModerationStatus.choices, default=ModerationStatus.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Opportunity(models.Model):
    academy = models.ForeignKey(Academy, related_name="opportunities", on_delete=models.CASCADE)
    kind = models.CharField(max_length=12, choices=OpportunityKind.choices, default=OpportunityKind.TEACHING)
    title = models.CharField(max_length=180)
    subject = models.CharField(max_length=100)
    description = models.TextField()
    city = models.CharField(max_length=100)
    budget = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, validators=[MinValueValidator(0)])
    mode = models.CharField(max_length=10, choices=DeliveryMode.choices, default=DeliveryMode.ONSITE)
    status = models.CharField(max_length=12, choices=ModerationStatus.choices, default=ModerationStatus.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class OpportunityApplication(models.Model):
    opportunity = models.ForeignKey(Opportunity, related_name="applications", on_delete=models.CASCADE)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="opportunity_applications", on_delete=models.CASCADE)
    message = models.TextField(max_length=2000)
    share_resume = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["opportunity", "applicant"], name="marketplace_unique_application")]


def academy_photo_upload_to(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"marketplace/academies/{instance.academy_id}/{uuid.uuid4().hex}.{extension}"


class AcademyPhoto(models.Model):
    academy = models.ForeignKey(Academy, related_name="photos", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=academy_photo_upload_to)
    caption = models.CharField(max_length=140, blank=True)
    status = models.CharField(max_length=12, choices=ModerationStatus.choices, default=ModerationStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)


class CollaborationProject(models.Model):
    """Moderated public invitation for a small educational collaboration."""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="collaboration_projects")
    title = models.CharField(max_length=180)
    specialty = models.CharField(max_length=100)
    description = models.TextField(max_length=3000)
    city = models.CharField(max_length=100, blank=True)
    mode = models.CharField(max_length=10, choices=DeliveryMode.choices, default=DeliveryMode.ONLINE)
    max_members = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(2), MaxValueValidator(20)])
    status = models.CharField(max_length=12, choices=ModerationStatus.choices, default=ModerationStatus.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CollaborationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار بررسی"
        ACCEPTED = "accepted", "پذیرفته‌شده"
        REJECTED = "rejected", "ردشده"

    project = models.ForeignKey(CollaborationProject, on_delete=models.CASCADE, related_name="requests")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collaboration_requests")
    message = models.TextField(max_length=1500)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["project", "applicant"], name="marketplace_unique_collab_request")]
