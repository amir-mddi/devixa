import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions
import django.db.models.query_utils
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
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="ReferralCode",
            fields=BASE_FIELDS + [
                ("code", models.CharField(db_index=True, max_length=16, unique=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="referral_code_record", to=settings.AUTH_USER_MODEL)),
            ] + audit_fields(),
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ReferralInvite",
            fields=BASE_FIELDS + [
                ("registered_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("invitee", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="referral_invite_received", to=settings.AUTH_USER_MODEL)),
                ("inviter", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="referral_invites_sent", to=settings.AUTH_USER_MODEL)),
                ("referral_code", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invites", to="referrals.referralcode")),
            ] + audit_fields(),
            options={"ordering": ["-registered_at"]},
        ),
        migrations.AddConstraint(
            model_name="referralinvite",
            constraint=models.CheckConstraint(condition=~django.db.models.query_utils.Q(("inviter", django.db.models.expressions.F("invitee"))), name="referral_inviter_not_invitee"),
        ),
        migrations.AddIndex(model_name="referralcode", index=models.Index(fields=["code", "is_active", "is_deleted"], name="referral_code_active_idx")),
        migrations.AddIndex(model_name="referralinvite", index=models.Index(fields=["inviter", "registered_at"], name="referral_inviter_date_idx")),
    ]
