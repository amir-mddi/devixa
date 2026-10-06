from django.contrib import admin

from backend.apps.referrals.models import (
    ReferralCode,
    ReferralInvite,
    TelegramChannelReferralLink,
    TelegramChannelReferralMember,
)


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


@admin.register(TelegramChannelReferralLink)
class TelegramChannelReferralLinkAdmin(admin.ModelAdmin):
    list_display = ("owner", "channel_username", "telegram_name", "is_revoked", "created_at")
    search_fields = ("owner__username", "owner__email", "channel_username", "invite_link")
    list_filter = ("channel_username", "is_revoked", "is_active")
    readonly_fields = ("invite_link", "telegram_name", "created_at", "updated_at")


@admin.register(TelegramChannelReferralMember)
class TelegramChannelReferralMemberAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_user_id",
        "username",
        "channel_username",
        "referral_owner",
        "is_current_member",
        "first_joined_at",
        "left_at",
    )
    search_fields = (
        "telegram_user_id",
        "username",
        "first_name",
        "last_name",
        "referral_link__owner__username",
        "referral_link__owner__email",
    )
    list_filter = ("channel_username", "is_current_member")
    readonly_fields = (
        "channel_username",
        "channel_chat_id",
        "telegram_user_id",
        "username",
        "first_name",
        "last_name",
        "referral_link",
        "first_joined_at",
        "last_joined_at",
        "left_at",
        "is_current_member",
        "created_at",
        "updated_at",
    )

    @admin.display(description="معرف")
    def referral_owner(self, obj):
        return obj.referral_link.owner if obj.referral_link_id else "—"
