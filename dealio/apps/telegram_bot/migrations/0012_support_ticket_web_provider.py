from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("telegram_bot", "0011_support_ticket_faq_tag")]

    operations = [
        migrations.AlterField(
            model_name="botsupportticket",
            name="profile",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="support_tickets",
                to="telegram_bot.telegramprofile",
            ),
        ),
    ]
