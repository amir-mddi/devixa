from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [("marketplace", "0004_alter_academy_id_alter_academyphoto_id_and_more"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(name="CollaborationProject", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=180)),
            ("specialty", models.CharField(max_length=100)),
            ("description", models.TextField(max_length=3000)),
            ("city", models.CharField(blank=True, max_length=100)),
            ("mode", models.CharField(choices=[("online", "آنلاین"), ("onsite", "حضوری"), ("both", "آنلاین و حضوری")], default="online", max_length=10)),
            ("max_members", models.PositiveSmallIntegerField(default=5, validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(20)])),
            ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("published", "منتشرشده"), ("rejected", "ردشده")], default="pending", max_length=12, db_index=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="collaboration_projects", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="CollaborationRequest", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("message", models.TextField(max_length=1500)),
            ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("accepted", "پذیرفته‌شده"), ("rejected", "ردشده")], default="pending", max_length=10, db_index=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("applicant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="collaboration_requests", to=settings.AUTH_USER_MODEL)),
            ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="requests", to="marketplace.collaborationproject")),
        ]),
        migrations.AddConstraint(model_name="collaborationrequest", constraint=models.UniqueConstraint(fields=("project", "applicant"), name="marketplace_unique_collab_request")),
    ]
