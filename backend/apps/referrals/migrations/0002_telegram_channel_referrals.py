import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


BASE_FIELDS = [
    ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
    ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
    ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
    ("deleted_at", models.DateTimeField(blank=True, null=True)),
    ("is_active", models.BooleanField(blank=True, default=True)),
    ("is_deleted", models.BooleanField(default=False)),
]


def audit_fields():
    return [
        ("user_created_object", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_user_created", to=settings.AUTH_USER_MODEL)),
        ("user_updated_object", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_updated", to=settings.AUTH_USER_MODEL)),
    ]


class Migration(migrations.Migration):
    dependencies = [
        ("referrals", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramChannelReferralLink",
            fields=BASE_FIELDS + [
                ("channel_username", models.CharField(max_length=64)),
                ("channel_chat_id", models.CharField(blank=True, default="", max_length=64)),
                ("invite_link", models.URLField(max_length=512, unique=True)),
                ("telegram_name", models.CharField(blank=True, default="", max_length=32)),
                ("is_revoked", models.BooleanField(default=False)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="telegram_channel_referral_links", to=settings.AUTH_USER_MODEL)),
            ] + audit_fields(),
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="TelegramChannelReferralMember",
            fields=BASE_FIELDS + [
                ("channel_username", models.CharField(max_length=64)),
                ("channel_chat_id", models.CharField(blank=True, default="", max_length=64)),
                ("telegram_user_id", models.BigIntegerField()),
                ("username", models.CharField(blank=True, default="", max_length=150)),
                ("first_name", models.CharField(blank=True, default="", max_length=150)),
                ("last_name", models.CharField(blank=True, default="", max_length=150)),
                ("first_joined_at", models.DateTimeField(blank=True, null=True)),
                ("last_joined_at", models.DateTimeField(blank=True, null=True)),
                ("left_at", models.DateTimeField(blank=True, null=True)),
                ("is_current_member", models.BooleanField(default=False)),
                ("referral_link", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="members", to="referrals.telegramchannelreferrallink")),
            ] + audit_fields(),
            options={"ordering": ["-first_joined_at", "-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="telegramchannelreferrallink",
            constraint=models.UniqueConstraint(fields=("owner", "channel_username"), name="ref_chlink_owner_uniq"),
        ),
        migrations.AddConstraint(
            model_name="telegramchannelreferralmember",
            constraint=models.UniqueConstraint(fields=("channel_username", "telegram_user_id"), name="ref_chmem_user_uniq"),
        ),
        migrations.AddIndex(
            model_name="telegramchannelreferrallink",
            index=models.Index(fields=["owner", "channel_username", "is_revoked"], name="ref_chlink_owner_idx"),
        ),
        migrations.AddIndex(
            model_name="telegramchannelreferralmember",
            index=models.Index(fields=["referral_link", "first_joined_at"], name="ref_chmem_link_idx"),
        ),
        migrations.AddIndex(
            model_name="telegramchannelreferralmember",
            index=models.Index(fields=["channel_username", "is_current_member"], name="ref_chmem_state_idx"),
        ),
    ]
