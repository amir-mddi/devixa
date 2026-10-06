from django.contrib import admin

from backend.apps.referrals.models import ReferralCode, ReferralInvite


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "created_at", "is_active")
    search_fields = ("code", "user__username", "user__email")
    readonly_fields = ("code", "created_at", "updated_at")


@admin.register(ReferralInvite)
class ReferralInviteAdmin(admin.ModelAdmin):
    list_display = ("inviter", "invitee", "referral_code", "registered_at", "is_active")
    search_fields = ("inviter__username", "invitee__username", "referral_code__code")
    list_filter = ("registered_at", "is_active")
    readonly_fields = ("registered_at", "created_at", "updated_at")
