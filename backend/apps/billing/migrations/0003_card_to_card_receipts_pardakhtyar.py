# Generated manually for card-to-card receipts and Pardakhtyar payment support.

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid

import backend.apps.billing.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("billing", "0002_alter_order_discount_amount_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="provider",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("card_to_card", "Card_To_Card"),
                    ("pardakhtyar", "Pardakhtyar"),
                    ("sandbox", "Sandbox"),
                ],
                default="card_to_card",
                max_length=40,
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="status",
            field=models.CharField(
                choices=[
                    ("initiated", "Initiated"),
                    ("pending_receipt", "Pending_Receipt"),
                    ("pending_verification", "Pending_Verification"),
                    ("receipt_rejected", "Receipt_Rejected"),
                    ("succeeded", "Succeeded"),
                    ("failed", "Failed"),
                    ("cancelled", "Cancelled"),
                    ("refunded", "Refunded"),
                ],
                db_index=True,
                default="initiated",
                max_length=30,
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["provider", "authority"], name="payment_provider_auth_idx"),
        ),
        migrations.CreateModel(
            name="PaymentReceipt",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("receipt_file", models.FileField(blank=True, default="", upload_to=backend.apps.billing.models.payment_receipt_upload_to)),
                ("receipt_file_url", models.URLField(blank=True, default="")),
                ("tracking_code", models.CharField(blank=True, default="", max_length=120)),
                ("payer_card_last4", models.CharField(blank=True, default="", max_length=4)),
                ("paid_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("note", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                        db_index=True,
                        default="pending",
                        max_length=30,
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("web", "Web"),
                            ("telegram", "Telegram"),
                            ("bale", "Bale"),
                            ("rubika", "Rubika"),
                        ],
                        default="web",
                        max_length=30,
                    ),
                ),
                ("admin_note", models.TextField(blank=True, default="")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "payment",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="receipts", to="billing.payment"),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="billing_payment_receipts_reviewed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payment_receipts", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_user_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="paymentreceipt",
            index=models.Index(fields=["payment", "status"], name="receipt_payment_status_idx"),
        ),
        migrations.AddIndex(
            model_name="paymentreceipt",
            index=models.Index(fields=["user", "status"], name="receipt_user_status_idx"),
        ),
    ]
