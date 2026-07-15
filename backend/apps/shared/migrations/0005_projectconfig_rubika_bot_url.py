from django.db import migrations, models

from backend.apps.shared.vo.project_config_vo import ProjectConfigDefaultVO


class Migration(migrations.Migration):
    dependencies = [("shared", "0004_projectconfig_bot_links")]

    operations = [
        migrations.AddField(
            model_name="projectconfigmodel",
            name="rubika_bot_url",
            field=models.URLField(
                blank=True,
                default=ProjectConfigDefaultVO.EMPTY_URL.value,
                max_length=500,
            ),
        ),
    ]
