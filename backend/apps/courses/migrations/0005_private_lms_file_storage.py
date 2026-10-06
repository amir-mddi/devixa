from django.db import migrations, models

import backend.apps.courses.adapters.private_storage
import backend.apps.courses.models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0004_lms_classroom"),
    ]

    operations = [
        migrations.AlterField(
            model_name="courseresource",
            name="file",
            field=models.FileField(
                blank=True,
                null=True,
                storage=backend.apps.courses.adapters.private_storage.get_private_course_storage,
                upload_to=backend.apps.courses.models.course_resource_upload_to,
            ),
        ),
        migrations.AlterField(
            model_name="courseassignment",
            name="attachment",
            field=models.FileField(
                blank=True,
                null=True,
                storage=backend.apps.courses.adapters.private_storage.get_private_course_storage,
                upload_to=backend.apps.courses.models.course_assignment_upload_to,
            ),
        ),
        migrations.AlterField(
            model_name="coursesubmission",
            name="file",
            field=models.FileField(
                blank=True,
                null=True,
                storage=backend.apps.courses.adapters.private_storage.get_private_course_storage,
                upload_to=backend.apps.courses.models.course_submission_upload_to,
            ),
        ),
        migrations.AlterField(
            model_name="coursequestionmessage",
            name="attachment",
            field=models.FileField(
                blank=True,
                null=True,
                storage=backend.apps.courses.adapters.private_storage.get_private_course_storage,
                upload_to=backend.apps.courses.models.course_resource_upload_to,
            ),
        ),
    ]
