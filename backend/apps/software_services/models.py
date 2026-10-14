import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from backend.apps.software_services.enums.request_enums import (
    ProjectBudget, ProjectTimeline, RequestStatus, ServiceCategory,
)


class SoftwareProjectRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="software_project_requests",
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    category = models.CharField(max_length=24, choices=ServiceCategory.choices)
    project_title = models.CharField(max_length=180)
    description = models.TextField(max_length=6000)
    budget = models.CharField(max_length=24, choices=ProjectBudget.choices, default=ProjectBudget.UNDECIDED)
    timeline = models.CharField(max_length=24, choices=ProjectTimeline.choices, default=ProjectTimeline.FLEXIBLE)
    reference_url = models.URLField(blank=True)
    status = models.CharField(max_length=24, choices=RequestStatus.choices, default=RequestStatus.NEW, db_index=True)
    staff_note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("status", "created_at"), name="software_request_status_idx")]
        verbose_name = "درخواست خدمات نرم‌افزاری"
        verbose_name_plural = "درخواست‌های خدمات نرم‌افزاری"

    def __str__(self):
        return f"{self.project_title} — {self.full_name}"
