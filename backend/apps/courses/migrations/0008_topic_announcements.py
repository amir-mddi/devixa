from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("courses", "0007_topic_resources_assignments")]

    operations = [
        migrations.AddField(
            model_name="courseannouncement", name="section",
            field=models.ForeignKey(
                to="courses.coursesection", related_name="announcements",
                null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL,
            ),
        ),
    ]
