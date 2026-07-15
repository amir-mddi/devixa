# Generated manually for discount code support.

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("courses", "0001_initial"),
        ("billing", "0003_card_to_card_receipts_pardakhtyar"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiscountCode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("code", models.CharField(db_index=True, max_length=60, unique=True)),
                ("title", models.CharField(blank=True, default="", max_length=160)),
                ("discount_type", models.CharField(choices=[("percent", "Percent"), ("amount", "Amount")], default="percent", max_length=20)),
                ("value", models.DecimalField(decimal_places=2, max_digits=12)),
                ("max_discount_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("minimum_order_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("usage_limit", models.PositiveIntegerField(blank=True, null=True)),
                ("used_count", models.PositiveIntegerField(default=0)),
                ("per_user_limit", models.PositiveIntegerField(default=1)),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("applies_to_all_courses", models.BooleanField(default=True)),
                ("courses", models.ManyToManyField(blank=True, related_name="discount_codes", to="courses.course")),
                ("user_created_object", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_user_created", to=settings.AUTH_USER_MODEL)),
                ("user_updated_object", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_updated", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DiscountRedemption",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("code", models.CharField(db_index=True, max_length=60)),
                ("amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("discount", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="redemptions", to="billing.discountcode")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="discount_redemptions", to="billing.order")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="discount_redemptions", to=settings.AUTH_USER_MODEL)),
                ("user_created_object", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_user_created", to=settings.AUTH_USER_MODEL)),
                ("user_updated_object", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_updated", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="discountcode", index=models.Index(fields=["code", "is_active", "is_deleted"], name="discount_code_active_idx")),
        migrations.AddIndex(model_name="discountredemption", index=models.Index(fields=["user", "code"], name="discount_user_code_idx")),
        migrations.AddConstraint(model_name="discountredemption", constraint=models.UniqueConstraint(fields=("discount", "order"), name="unique_discount_order_redemption")),
    ]
