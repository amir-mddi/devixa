from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("courses", "0006_rename_submission_status_index")]

    operations = [
        migrations.AddField(
            model_name="courseresource", name="section",
            field=models.ForeignKey(to="courses.coursesection", related_name="resources", null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AddField(
            model_name="courseassignment", name="section",
            field=models.ForeignKey(to="courses.coursesection", related_name="assignments", null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]
