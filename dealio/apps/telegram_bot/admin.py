from django.contrib import admin

from dealio.apps.telegram_bot.models import BotRuntimeSetting, BotScheduledNotification, BotSupportMessage, BotSupportTicket, ChannelSyncMessage, TelegramProfile, TelegramUpdateLog


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = (
        "messenger_provider",
        "telegram_user_id",
        "chat_id",
        "username",
        "bot_language",
        "user",
        "is_verified",
        "is_active",
        "created_at",
    )
    list_filter = ("messenger_provider", "bot_language", "is_verified", "is_active", "created_at")
    search_fields = ("messenger_provider", "username", "first_name", "last_name", "chat_id", "telegram_user_id", "user__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TelegramUpdateLog)
class TelegramUpdateLogAdmin(admin.ModelAdmin):
    list_display = ("messenger_provider", "update_id", "processed", "created_at")
    list_filter = ("messenger_provider", "processed", "created_at")
    search_fields = ("update_id", "error_text")
    readonly_fields = ("payload", "created_at")


@admin.register(ChannelSyncMessage)
class ChannelSyncMessageAdmin(admin.ModelAdmin):
    list_display = (
        "source_provider",
        "source_chat_id",
        "source_message_id",
        "target_provider",
        "target_chat_id",
        "target_message_id",
        "updated_at",
    )
    list_filter = ("source_provider", "target_provider", "created_at", "updated_at")
    search_fields = ("source_chat_id", "source_message_id", "target_chat_id", "target_message_id", "last_error")
    readonly_fields = ("raw_response", "created_at", "updated_at")



@admin.register(BotRuntimeSetting)
class BotRuntimeSettingAdmin(admin.ModelAdmin):
    list_display = ("provider", "key", "is_secret", "is_active", "updated_by", "updated_at")
    list_filter = ("provider", "is_secret", "is_active", "updated_at")
    search_fields = ("provider", "key")
    readonly_fields = ("created_at", "updated_at")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.is_secret and "value" in form.base_fields:
            form.base_fields["value"].help_text = "Secret value is stored encoded. Prefer updating secrets from the bot settings panel/API."
        return form


@admin.register(BotScheduledNotification)
class BotScheduledNotificationAdmin(admin.ModelAdmin):
    list_display = ("provider", "status", "scheduled_at", "recipient_count", "success_count", "failed_count", "created_by")
    list_filter = ("provider", "status", "scheduled_at")
    search_fields = ("message", "last_error")
    readonly_fields = ("created_at", "updated_at", "sent_at")


class BotSupportMessageInline(admin.TabularInline):
    model = BotSupportMessage
    extra = 0
    readonly_fields = ("sender_type", "sender_user", "message", "created_at")


@admin.register(BotSupportTicket)
class BotSupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "user", "profile", "status", "is_frequently_asked", "faq_display_order", "last_message_at", "created_at")
    list_filter = ("provider", "status", "is_frequently_asked", "created_at", "last_message_at")
    search_fields = ("subject", "faq_question", "faq_answer", "user__email", "profile__chat_id", "profile__username")
    readonly_fields = ("created_at", "updated_at", "closed_at")
    fieldsets = (
        (
            "Ticket",
            {
                "fields": (
                    "provider",
                    "profile",
                    "user",
                    "subject",
                    "status",
                    "last_message_at",
                    "closed_by",
                    "closed_at",
                )
            },
        ),
        (
            "Frequently asked question",
            {
                "fields": (
                    "is_frequently_asked",
                    "faq_question",
                    "faq_answer",
                    "faq_display_order",
                ),
                "description": "اگر این تیکت سوال پرتکرار است، این بخش را کامل کنید تا در FAQ سایت نمایش داده شود.",
            },
        ),
        ("Status", {"fields": ("created_at", "updated_at")}),
    )
    inlines = [BotSupportMessageInline]


@admin.register(BotSupportMessage)
class BotSupportMessageAdmin(admin.ModelAdmin):
    list_display = ("ticket", "sender_type", "sender_user", "created_at")
    list_filter = ("sender_type", "created_at")
    search_fields = ("message", "ticket__subject")
    readonly_fields = ("created_at",)
