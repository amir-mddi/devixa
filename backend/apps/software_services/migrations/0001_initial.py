import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="SoftwareProjectRequest",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("full_name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=32)),
                ("category", models.CharField(max_length=24, choices=[("website", "طراحی سایت"), ("webapp", "وب‌اپلیکیشن"), ("mobile", "اپلیکیشن موبایل"), ("telegram", "ربات و اتوماسیون"), ("backend", "بک‌اند و API"), ("uiux", "رابط کاربری و تجربه کاربری"), ("other", "سایر خدمات فنی")])),
                ("project_title", models.CharField(max_length=180)),
                ("description", models.TextField(max_length=6000)),
                ("budget", models.CharField(max_length=24, default="undecided", choices=[("undecided", "نیاز به مشاوره"), ("small", "کمتر از ۲۰ میلیون تومان"), ("medium", "۲۰ تا ۶۰ میلیون تومان"), ("large", "۶۰ تا ۱۵۰ میلیون تومان"), ("enterprise", "بیشتر از ۱۵۰ میلیون تومان")])),
                ("timeline", models.CharField(max_length=24, default="flexible", choices=[("flexible", "زمان‌بندی منعطف"), ("one_month", "تا یک ماه"), ("three_months", "۱ تا ۳ ماه"), ("long_term", "بیش از ۳ ماه")])),
                ("reference_url", models.URLField(blank=True)),
                ("status", models.CharField(max_length=24, default="new", db_index=True, choices=[("new", "جدید"), ("contacted", "تماس گرفته شده"), ("proposal", "پیشنهاد ارسال شده"), ("in_progress", "در حال انجام"), ("completed", "تکمیل شده"), ("declined", "بسته شده")])),
                ("staff_note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name="software_project_requests", null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={"ordering": ("-created_at",), "verbose_name": "درخواست خدمات نرم‌افزاری", "verbose_name_plural": "درخواست‌های خدمات نرم‌افزاری"},
        ),
        migrations.AddIndex(model_name="softwareprojectrequest", index=models.Index(fields=["status", "created_at"], name="software_request_status_idx")),
    ]
