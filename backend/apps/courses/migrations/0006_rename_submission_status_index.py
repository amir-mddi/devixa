from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0005_private_lms_file_storage"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="coursesubmission",
            old_name="submission_assignment_status_idx",
            new_name="course_subm_asgn_status_idx",
        ),
    ]
