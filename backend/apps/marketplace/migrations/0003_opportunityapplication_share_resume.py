from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("marketplace", "0002_academyphoto")]
    operations = [
        migrations.AddField(
            model_name="opportunityapplication",
            name="share_resume",
            field=models.BooleanField(default=False),
        ),
    ]
