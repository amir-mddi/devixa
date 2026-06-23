from django.contrib import admin

from dealio.apps.telegram_bot.models import TelegramProfile, TelegramUpdateLog


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_user_id",
        "chat_id",
        "username",
        "bot_language",
        "user",
        "is_verified",
        "is_active",
        "created_at",
    )
    list_filter = ("bot_language", "is_verified", "is_active", "created_at")
    search_fields = ("username", "first_name", "last_name", "chat_id", "telegram_user_id", "user__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TelegramUpdateLog)
class TelegramUpdateLogAdmin(admin.ModelAdmin):
    list_display = ("update_id", "processed", "created_at")
    list_filter = ("processed", "created_at")
    search_fields = ("update_id", "error_text")
    readonly_fields = ("payload", "created_at")
