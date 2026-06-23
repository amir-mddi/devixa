# Generated manually for Telegram bot language preference.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_bot", "0002_rename_telegram_bo_telegr_0ab58f_idx_telegram_bo_telegra_9ead8b_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="telegramprofile",
            name="bot_language",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
    ]
