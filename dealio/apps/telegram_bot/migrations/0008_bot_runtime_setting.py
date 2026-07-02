# Generated manually for runtime-editable bot settings.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("telegram_bot", "0007_rename_telegram_bo_source__6afdc3_idx_telegram_bo_source__7c9aaf_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="BotRuntimeSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(db_index=True, max_length=40)),
                ("key", models.CharField(db_index=True, max_length=120)),
                ("value", models.TextField(blank=True, default="")),
                ("is_secret", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_bot_runtime_settings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["provider", "key"],
            },
        ),
        migrations.AddIndex(
            model_name="botruntimesetting",
            index=models.Index(fields=["provider", "key"], name="telegram_bo_provide_5e3eb8_idx"),
        ),
        migrations.AddIndex(
            model_name="botruntimesetting",
            index=models.Index(fields=["provider", "is_active"], name="telegram_bo_provide_933cb2_idx"),
        ),
        migrations.AddConstraint(
            model_name="botruntimesetting",
            constraint=models.UniqueConstraint(fields=("provider", "key"), name="unique_bot_runtime_setting_provider_key"),
        ),
    ]
