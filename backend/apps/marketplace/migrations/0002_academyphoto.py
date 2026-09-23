import django.db.models.deletion
from django.db import migrations, models
from backend.apps.marketplace.models import academy_photo_upload_to


class Migration(migrations.Migration):
    dependencies = [("marketplace", "0001_initial")]
    operations = [migrations.CreateModel(name="AcademyPhoto", fields=[
        ("id", models.BigAutoField(primary_key=True, serialize=False)),
        ("image", models.ImageField(upload_to=academy_photo_upload_to)),
        ("caption", models.CharField(blank=True, max_length=140)),
        ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("published", "منتشرشده"), ("rejected", "ردشده")], default="pending", max_length=12)),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("academy", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="photos", to="marketplace.academy")),
    ])]
