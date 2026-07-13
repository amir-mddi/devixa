from django.conf import settings
from django.db import models


class TelegramProfile(models.Model):
    """Stores the Telegram chat that is linked to a application user account."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="telegram_profiles",
    )
    telegram_user_id = models.CharField(max_length=120, db_index=True)
    messenger_provider = models.CharField(
        max_length=30, default="telegram", db_index=True
    )
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
            models.Index(
                fields=["telegram_user_id"], name="telegram_bo_telegra_9ead8b_idx"
            ),
            models.Index(fields=["chat_id"], name="telegram_bo_chat_id_123572_idx"),
            models.Index(
                fields=["messenger_provider", "chat_id"],
                name="telegram_bo_messeng_39538d_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["messenger_provider", "chat_id"],
                name="unique_bot_profile_provider_chat",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        name = self.username or self.first_name or str(self.telegram_user_id)
        return f"TelegramProfile({self.messenger_provider}:{name}, chat={self.chat_id})"


class TelegramUpdateLog(models.Model):
    """Keeps webhook processing idempotent because Telegram can retry updates."""

    messenger_provider = models.CharField(
        max_length=30, default="telegram", db_index=True
    )
    update_id = models.BigIntegerField(db_index=True)
    payload = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)
    error_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["messenger_provider", "update_id"],
                name="unique_bot_update_provider_update",
            ),
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
            models.Index(
                fields=["source_provider", "source_chat_id", "source_message_id"],
                name="telegram_bo_source__7c9aaf_idx",
            ),
            models.Index(
                fields=["target_provider", "target_chat_id", "target_message_id"],
                name="telegram_bo_target__f12eff_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "source_provider",
                    "source_chat_id",
                    "source_message_id",
                    "target_provider",
                    "target_chat_id",
                ],
                name="unique_channel_sync_source_target",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"ChannelSyncMessage({self.source_provider}:{self.source_chat_id}:{self.source_message_id}"
            f" -> {self.target_provider}:{self.target_chat_id}:{self.target_message_id})"
        )


class BotRuntimeSetting(models.Model):
    """Runtime-editable bot setting.

    Env values remain fallback/bootstrap values. This table is the source of
    truth for settings changed from the admin/panel UI.
    """

    provider = models.CharField(max_length=40, db_index=True)
    key = models.CharField(max_length=120, db_index=True)
    value = models.TextField(blank=True, default="")
    is_secret = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_bot_runtime_settings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["provider", "key"], name="telegram_bo_provide_5e3eb8_idx"
            ),
            models.Index(
                fields=["provider", "is_active"], name="telegram_bo_provide_933cb2_idx"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "key"],
                name="unique_bot_runtime_setting_provider_key",
            ),
        ]
        ordering = ["provider", "key"]

    def __str__(self):
        return f"BotRuntimeSetting({self.provider}.{self.key})"


class BotScheduledNotification(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    provider = models.CharField(max_length=30, default="telegram", db_index=True)
    message = models.TextField()
    scheduled_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    recipient_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_bot_scheduled_notifications",
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(
                fields=["provider", "status", "scheduled_at"],
                name="bot_sched_provider_status_idx",
            ),
        ]

    def __str__(self):
        return f"BotScheduledNotification({self.provider}, {self.status}, {self.scheduled_at})"


class BotSupportTicket(models.Model):
    STATUS_OPEN = "open"
    STATUS_ANSWERED = "answered"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_ANSWERED, "Answered"),
        (STATUS_CLOSED, "Closed"),
    )

    provider = models.CharField(max_length=30, default="telegram", db_index=True)
    profile = models.ForeignKey(
        TelegramProfile,
        related_name="support_tickets",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bot_support_tickets",
    )
    subject = models.CharField(max_length=180, blank=True, default="")
    is_frequently_asked = models.BooleanField(default=False, db_index=True)
    faq_question = models.CharField(max_length=220, blank=True, default="")
    faq_answer = models.TextField(blank=True, default="")
    faq_display_order = models.PositiveSmallIntegerField(default=100)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True
    )
    last_message_at = models.DateTimeField(auto_now_add=True, db_index=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="closed_bot_support_tickets",
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_message_at"]
        indexes = [
            models.Index(
                fields=["provider", "status", "last_message_at"],
                name="support_provider_status_idx",
            ),
            models.Index(
                fields=["is_frequently_asked", "faq_display_order"],
                name="support_faq_order_idx",
            ),
        ]

    def __str__(self):
        return f"SupportTicket({self.provider}, {self.status}, {self.id})"


class BotSupportMessage(models.Model):
    SENDER_USER = "user"
    SENDER_ADMIN = "admin"
    SENDER_SYSTEM = "system"
    SENDER_CHOICES = (
        (SENDER_USER, "User"),
        (SENDER_ADMIN, "Admin"),
        (SENDER_SYSTEM, "System"),
    )

    ticket = models.ForeignKey(
        BotSupportTicket, related_name="messages", on_delete=models.CASCADE
    )
    sender_type = models.CharField(max_length=20, choices=SENDER_CHOICES, db_index=True)
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bot_support_messages",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["ticket", "created_at"], name="support_msg_ticket_created_idx"
            ),
        ]

    def __str__(self):
        return f"SupportMessage({self.sender_type}, {self.ticket_id})"
