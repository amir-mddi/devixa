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
    telegram_user_id = models.CharField(max_length=120, db_index=True)
    messenger_provider = models.CharField(max_length=30, default="telegram", db_index=True)
    chat_id = models.CharField(max_length=120, db_index=True)
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
            models.Index(fields=["messenger_provider", "chat_id"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["messenger_provider", "chat_id"], name="unique_bot_profile_provider_chat"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        name = self.username or self.first_name or str(self.telegram_user_id)
        return f"TelegramProfile({self.messenger_provider}:{name}, chat={self.chat_id})"


class TelegramUpdateLog(models.Model):
    """Keeps webhook processing idempotent because Telegram can retry updates."""

    messenger_provider = models.CharField(max_length=30, default="telegram", db_index=True)
    update_id = models.BigIntegerField(db_index=True)
    payload = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)
    error_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["messenger_provider", "update_id"], name="unique_bot_update_provider_update"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"TelegramUpdateLog(provider={self.messenger_provider}, update_id={self.update_id}, processed={self.processed})"


class ChannelSyncMessage(models.Model):
    """Maps a Telegram source channel message to mirrored Bale/Rubika messages.

    This allows edits in the Telegram source channel to edit the related messages
    already sent to target messenger channels.
    """

    source_provider = models.CharField(max_length=30, default="telegram", db_index=True)
    source_chat_id = models.CharField(max_length=160, db_index=True)
    source_message_id = models.CharField(max_length=160, db_index=True)
    target_provider = models.CharField(max_length=30, db_index=True)
    target_chat_id = models.CharField(max_length=160, db_index=True)
    target_message_id = models.CharField(max_length=160, blank=True, db_index=True)
    text_hash = models.CharField(max_length=64, blank=True)
    last_error = models.TextField(blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["source_provider", "source_chat_id", "source_message_id"]),
            models.Index(fields=["target_provider", "target_chat_id", "target_message_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_provider", "source_chat_id", "source_message_id", "target_provider", "target_chat_id"],
                name="unique_channel_sync_source_target",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"ChannelSyncMessage({self.source_provider}:{self.source_chat_id}:{self.source_message_id}"
            f" -> {self.target_provider}:{self.target_chat_id}:{self.target_message_id})"
        )
