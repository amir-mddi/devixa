from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import (Academy, AcademyPhoto, CollaborationProject, CollaborationRequest, MentorProfile, MentorReview, MentorshipBooking, MentorshipOffer,
                     MentorshipSlot, Opportunity, OpportunityApplication)


class ModerationAdmin(admin.ModelAdmin):
    actions = ["publish_items", "reject_items"]

    @admin.action(description="انتشار موارد انتخابی")
    def publish_items(self, request, queryset):
        queryset.update(status="published")

    @admin.action(description="رد موارد انتخابی")
    def reject_items(self, request, queryset):
        queryset.update(status="rejected")


@admin.register(MentorProfile)
class MentorProfileAdmin(ModerationAdmin):
    list_display = ("display_name", "owner", "city", "status")
    exclude = ("resume",)  # Private FileField has no public URL; avoid admin widget URL generation.
    readonly_fields = ("private_resume_link",)

    @admin.display(description="Private resume")
    def private_resume_link(self, obj):
        if obj and obj.resume:
            return format_html("<a href=\"{}\">Download resume</a>", reverse("marketplace:staff_resume_download", args=[obj.pk]))
        return "—"
    list_filter = ("status", "city")
    search_fields = ("display_name", "subjects")


@admin.register(MentorshipOffer)
class OfferAdmin(ModerationAdmin):
    list_display = ("title", "mentor", "hourly_price", "status")
    list_filter = ("status", "mode")


@admin.register(Academy)
class AcademyAdmin(ModerationAdmin):
    list_display = ("name", "owner", "city", "status")
    list_filter = ("status", "city")
    search_fields = ("name", "programs")


@admin.register(Opportunity)
class OpportunityAdmin(ModerationAdmin):
    list_display = ("title", "academy", "kind", "status")
    list_filter = ("status", "kind")


@admin.register(MentorReview)
class ReviewAdmin(ModerationAdmin):
    list_display = ("booking", "rating", "status")
    list_filter = ("status",)


@admin.register(MentorshipBooking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("student", "slot", "status", "created_at")
    readonly_fields = ("student", "slot", "created_at", "updated_at")


admin.site.register(MentorshipSlot)
admin.site.register(OpportunityApplication)


@admin.register(AcademyPhoto)
class AcademyPhotoAdmin(ModerationAdmin):
    list_display = ("academy", "caption", "status")
    list_filter = ("status",)


@admin.register(CollaborationProject)
class CollaborationProjectAdmin(ModerationAdmin):
    list_display = ("title", "owner", "specialty", "status", "created_at")
    list_filter = ("status", "mode")
    search_fields = ("title", "specialty")


@admin.register(CollaborationRequest)
class CollaborationRequestAdmin(admin.ModelAdmin):
    list_display = ("project", "applicant", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("project", "applicant", "message", "status", "created_at")
