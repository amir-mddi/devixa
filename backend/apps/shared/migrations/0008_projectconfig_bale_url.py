from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("shared", "0007_alter_projectconfigmodel_display_name_and_more")]

    operations = [
        migrations.AddField(
            model_name="projectconfigmodel",
            name="bale_url",
            field=models.URLField(blank=True, default="#", max_length=500),
        ),
    ]
