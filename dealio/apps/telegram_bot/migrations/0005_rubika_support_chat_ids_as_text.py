# Generated manually for Rubika messenger support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_bot", "0004_messenger_provider_bale_support"),
    ]

    operations = [
        migrations.AlterField(
            model_name="telegramprofile",
            name="telegram_user_id",
            field=models.CharField(db_index=True, max_length=120),
        ),
        migrations.AlterField(
            model_name="telegramprofile",
            name="chat_id",
            field=models.CharField(db_index=True, max_length=120),
        ),
    ]
