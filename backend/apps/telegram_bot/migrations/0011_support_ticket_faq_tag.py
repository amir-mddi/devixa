# Generated for marking support tickets as frequently asked public FAQ items.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_bot", "0010_telegramprofile_telegram_bo_chat_id_123572_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="botsupportticket",
            name="is_frequently_asked",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="botsupportticket",
            name="faq_question",
            field=models.CharField(blank=True, default="", max_length=220),
        ),
        migrations.AddField(
            model_name="botsupportticket",
            name="faq_answer",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="botsupportticket",
            name="faq_display_order",
            field=models.PositiveSmallIntegerField(default=100),
        ),
        migrations.AddIndex(
            model_name="botsupportticket",
            index=models.Index(fields=["is_frequently_asked", "faq_display_order"], name="support_faq_order_idx"),
        ),
    ]
