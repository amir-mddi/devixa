# Generated for social OAuth login support.

import uuid

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_remove_customuser_created_verified_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="phone_number",
            field=models.CharField(
                blank=True,
                help_text="Phone can be collected after social signup.",
                max_length=11,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        code="invalid_phone_number",
                        message="phone number must be digit and start with 09.........",
                        regex="^09[0-9]{9}$",
                    )
                ],
            ),
        ),
        migrations.CreateModel(
            name="SocialAccount",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "provider",
                    models.CharField(
                        choices=[("google", "Google"), ("github", "GitHub")],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("provider_user_id", models.CharField(max_length=255)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("extra_data", models.JSONField(blank=True, default=dict)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="social_accounts",
                        to="accounts.customuser",
                    ),
                ),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="accounts_socialaccount_user_created",
                        to="accounts.customuser",
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="accounts_socialaccount_updated",
                        to="accounts.customuser",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["provider", "email"], name="social_provider_email_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("provider", "provider_user_id"),
                        name="unique_social_provider_user_id",
                    ),
                ],
            },
        ),
    ]
