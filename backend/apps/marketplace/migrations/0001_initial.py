# Initial database schema for the Devixa educational marketplace.
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q
from backend.apps.marketplace.adapters.private_storage import resume_storage
from backend.apps.marketplace.models import resume_upload_to


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="MentorProfile", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("display_name", models.CharField(max_length=140)),
            ("headline", models.CharField(max_length=200)),
            ("bio", models.TextField()),
            ("subjects", models.CharField(help_text="موضوعات تدریس، جداشده با ویرگول", max_length=250)),
            ("experience_years", models.PositiveSmallIntegerField(default=0)),
            ("city", models.CharField(blank=True, max_length=100)),
            ("portfolio_url", models.URLField(blank=True)),
            ("resume", models.FileField(blank=True, storage=resume_storage, upload_to=resume_upload_to)),
            ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("published", "منتشرشده"), ("rejected", "ردشده")], db_index=True, default="pending", max_length=12)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("owner", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="mentor_profile", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="Academy", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("name", models.CharField(max_length=180)),
            ("category", models.CharField(help_text="مدرسه، هنرستان، آموزشگاه یا سایر", max_length=100)),
            ("description", models.TextField()),
            ("programs", models.TextField(help_text="رشته‌ها و دوره‌های ارائه‌شده")),
            ("facilities", models.TextField(blank=True)),
            ("city", models.CharField(db_index=True, max_length=100)),
            ("address", models.CharField(max_length=300)),
            ("website", models.URLField(blank=True)),
            ("public_phone", models.CharField(blank=True, max_length=25)),
            ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("published", "منتشرشده"), ("rejected", "ردشده")], db_index=True, default="pending", max_length=12)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_academies", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="MentorshipOffer", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("title", models.CharField(max_length=180)),
            ("subject", models.CharField(db_index=True, max_length=100)),
            ("description", models.TextField()),
            ("hourly_price", models.DecimalField(decimal_places=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
            ("city", models.CharField(blank=True, max_length=100)),
            ("mode", models.CharField(choices=[("online", "آنلاین"), ("onsite", "حضوری"), ("both", "آنلاین و حضوری")], default="online", max_length=10)),
            ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("published", "منتشرشده"), ("rejected", "ردشده")], db_index=True, default="pending", max_length=12)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("mentor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="offers", to="marketplace.mentorprofile")),
        ]),
        migrations.CreateModel(name="MentorshipSlot", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("starts_at", models.DateTimeField(db_index=True)),
            ("ends_at", models.DateTimeField()),
            ("offer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="slots", to="marketplace.mentorshipoffer")),
        ], options={"ordering": ["starts_at"]}),
        migrations.CreateModel(name="MentorshipBooking", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("status", models.CharField(choices=[("requested", "درخواست‌شده"), ("confirmed", "تأییدشده"), ("cancelled", "لغوشده"), ("completed", "برگزارشده")], default="requested", max_length=12)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("slot", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="marketplace.mentorshipslot")),
            ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mentorship_bookings", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="MentorReview", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("rating", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
            ("comment", models.TextField(max_length=2000)),
            ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("published", "منتشرشده"), ("rejected", "ردشده")], default="pending", max_length=12)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("booking", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="review", to="marketplace.mentorshipbooking")),
        ]),
        migrations.CreateModel(name="Opportunity", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("kind", models.CharField(choices=[("teaching", "استخدام مدرس"), ("technical", "خدمات فنی و پشتیبانی"), ("other", "سایر همکاری‌ها")], default="teaching", max_length=12)),
            ("title", models.CharField(max_length=180)),
            ("subject", models.CharField(max_length=100)),
            ("description", models.TextField()),
            ("city", models.CharField(max_length=100)),
            ("budget", models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True, validators=[django.core.validators.MinValueValidator(0)])),
            ("mode", models.CharField(choices=[("online", "آنلاین"), ("onsite", "حضوری"), ("both", "آنلاین و حضوری")], default="onsite", max_length=10)),
            ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("published", "منتشرشده"), ("rejected", "ردشده")], db_index=True, default="pending", max_length=12)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("academy", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="opportunities", to="marketplace.academy")),
        ]),
        migrations.CreateModel(name="OpportunityApplication", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("message", models.TextField(max_length=2000)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("applicant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="opportunity_applications", to=settings.AUTH_USER_MODEL)),
            ("opportunity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="marketplace.opportunity")),
        ]),
        migrations.AddConstraint(model_name="mentorshipslot", constraint=models.UniqueConstraint(fields=("offer", "starts_at"), name="marketplace_unique_offer_slot")),
        migrations.AddConstraint(model_name="mentorshipbooking", constraint=models.UniqueConstraint(condition=Q(status__in=["requested", "confirmed", "completed"]), fields=("slot",), name="marketplace_one_active_booking_per_slot")),
        migrations.AddConstraint(model_name="opportunityapplication", constraint=models.UniqueConstraint(fields=("opportunity", "applicant"), name="marketplace_unique_application")),
    ]
