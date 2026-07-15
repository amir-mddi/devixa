# Generated manually for bot support tickets and scheduled notifications.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("telegram_bot", "0008_bot_runtime_setting"),
    ]

    operations = [
        migrations.CreateModel(
            name="BotScheduledNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(db_index=True, default="telegram", max_length=30)),
                ("message", models.TextField()),
                ("scheduled_at", models.DateTimeField(db_index=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("sent", "Sent"), ("failed", "Failed"), ("cancelled", "Cancelled")], db_index=True, default="pending", max_length=30)),
                ("recipient_count", models.PositiveIntegerField(default=0)),
                ("success_count", models.PositiveIntegerField(default=0)),
                ("failed_count", models.PositiveIntegerField(default=0)),
                ("last_error", models.TextField(blank=True, default="")),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_bot_scheduled_notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-scheduled_at"]},
        ),
        migrations.CreateModel(
            name="BotSupportTicket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(db_index=True, default="telegram", max_length=30)),
                ("subject", models.CharField(blank=True, default="", max_length=180)),
                ("status", models.CharField(choices=[("open", "Open"), ("answered", "Answered"), ("closed", "Closed")], db_index=True, default="open", max_length=30)),
                ("last_message_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("closed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="closed_bot_support_tickets", to=settings.AUTH_USER_MODEL)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="support_tickets", to="telegram_bot.telegramprofile")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bot_support_tickets", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-last_message_at"]},
        ),
        migrations.CreateModel(
            name="BotSupportMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sender_type", models.CharField(choices=[("user", "User"), ("admin", "Admin"), ("system", "System")], db_index=True, max_length=20)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("sender_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bot_support_messages", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="telegram_bot.botsupportticket")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddIndex(model_name="botschedulednotification", index=models.Index(fields=["provider", "status", "scheduled_at"], name="bot_sched_provider_status_idx")),
        migrations.AddIndex(model_name="botsupportticket", index=models.Index(fields=["provider", "status", "last_message_at"], name="support_provider_status_idx")),
        migrations.AddIndex(model_name="botsupportmessage", index=models.Index(fields=["ticket", "created_at"], name="support_msg_ticket_created_idx")),
    ]
