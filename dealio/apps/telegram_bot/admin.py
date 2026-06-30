from django.contrib import admin

from dealio.apps.telegram_bot.models import ChannelSyncMessage, TelegramProfile, TelegramUpdateLog


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
