from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("courses", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("order_number", models.CharField(blank=True, max_length=60, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("cancelled", "Cancelled"),
                            ("expired", "Expired"),
                            ("refunded", "Refunded"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=30,
                    ),
                ),
                ("subtotal_amount", models.DecimalField(decimal_places=2, default="0.00", max_digits=12)),
                ("discount_amount", models.DecimalField(decimal_places=2, default="0.00", max_digits=12)),
                ("total_amount", models.DecimalField(decimal_places=2, default="0.00", max_digits=12)),
                (
                    "currency",
                    models.CharField(
                        choices=[("irr", "Irr"), ("usd", "Usd"), ("eur", "Eur")],
                        default="irr",
                        max_length=10,
                    ),
                ),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to=settings.AUTH_USER_MODEL),
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
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("course_title", models.CharField(max_length=180)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("total_price", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "course",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="courses.course"),
                ),
                (
                    "order",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="billing.order"),
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
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("payment_number", models.CharField(blank=True, max_length=60, unique=True)),
                (
                    "provider",
                    models.CharField(
                        choices=[("manual", "Manual"), ("sandbox", "Sandbox")],
                        default="manual",
                        max_length=40,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("initiated", "Initiated"),
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
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "currency",
                    models.CharField(
                        choices=[("irr", "Irr"), ("usd", "Usd"), ("eur", "Eur")],
                        default="irr",
                        max_length=10,
                    ),
                ),
                ("authority", models.CharField(blank=True, default="", max_length=255)),
                ("transaction_id", models.CharField(blank=True, default="", max_length=255)),
                ("payment_url", models.URLField(blank=True, default="")),
                ("request_payload", models.JSONField(blank=True, default=dict)),
                ("response_payload", models.JSONField(blank=True, default=dict)),
                ("failure_message", models.TextField(blank=True, default="")),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                (
                    "order",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="billing.order"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to=settings.AUTH_USER_MODEL),
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
        migrations.AddIndex(model_name="order", index=models.Index(fields=["user", "status"], name="order_user_status_idx")),
        migrations.AddIndex(model_name="order", index=models.Index(fields=["order_number"], name="order_number_idx")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.UniqueConstraint(fields=("order", "course"), name="unique_order_course_item")),
        migrations.AddIndex(model_name="payment", index=models.Index(fields=["user", "status"], name="payment_user_status_idx")),
        migrations.AddIndex(model_name="payment", index=models.Index(fields=["payment_number"], name="payment_number_idx")),
    ]
