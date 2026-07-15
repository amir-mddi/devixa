# Generated for database-driven public channel bot links.

from django.db import migrations, models

from backend.apps.shared.vo.project_config_vo import ProjectConfigDefaultVO


class Migration(migrations.Migration):

    dependencies = [
        ("shared", "0003_projectconfigmodel"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectconfigmodel",
            name="telegram_bot_url",
            field=models.URLField(blank=True, default=ProjectConfigDefaultVO.EMPTY_URL.value, max_length=500),
        ),
        migrations.AddField(
            model_name="projectconfigmodel",
            name="bale_bot_url",
            field=models.URLField(blank=True, default=ProjectConfigDefaultVO.EMPTY_URL.value, max_length=500),
        ),
    ]
