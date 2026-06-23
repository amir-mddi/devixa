from django.conf import settings
from django.db import models


class TelegramProfile(models.Model):
    """Stores the Telegram chat that is linked to a Dealio user account."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="telegram_profiles",
    )
    telegram_user_id = models.BigIntegerField(db_index=True)
    chat_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    language_code = models.CharField(max_length=20, blank=True)
    bot_language = models.CharField(max_length=10, blank=True, default="")
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["telegram_user_id"]),
            models.Index(fields=["chat_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        name = self.username or self.first_name or str(self.telegram_user_id)
        return f"TelegramProfile({name}, chat={self.chat_id})"


class TelegramUpdateLog(models.Model):
    """Keeps webhook processing idempotent because Telegram can retry updates."""

    update_id = models.BigIntegerField(unique=True)
    payload = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)
    error_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"TelegramUpdateLog(update_id={self.update_id}, processed={self.processed})"
