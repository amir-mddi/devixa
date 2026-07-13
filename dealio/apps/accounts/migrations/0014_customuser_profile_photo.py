from django.db import migrations, models

import dealio.apps.accounts.models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0013_alter_customuser_options")]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="profile_photo",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=dealio.apps.accounts.models.profile_photo_upload_to,
            ),
        ),
    ]
