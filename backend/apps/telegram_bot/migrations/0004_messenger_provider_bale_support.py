# Generated manually for multi-messenger bot support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_bot", "0003_telegramprofile_bot_language"),
    ]

    operations = [
        migrations.AddField(
            model_name="telegramprofile",
            name="messenger_provider",
            field=models.CharField(db_index=True, default="telegram", max_length=30),
        ),
        migrations.AlterField(
            model_name="telegramprofile",
            name="chat_id",
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.RemoveIndex(
            model_name="telegramprofile",
            name="telegram_bo_chat_id_123572_idx",
        ),
        migrations.AddIndex(
            model_name="telegramprofile",
            index=models.Index(fields=["messenger_provider", "chat_id"], name="telegram_bo_msg_prov_chat_idx"),
        ),
        migrations.AddConstraint(
            model_name="telegramprofile",
            constraint=models.UniqueConstraint(fields=["messenger_provider", "chat_id"], name="unique_bot_profile_provider_chat"),
        ),
        migrations.AddField(
            model_name="telegramupdatelog",
            name="messenger_provider",
            field=models.CharField(db_index=True, default="telegram", max_length=30),
        ),
        migrations.AlterField(
            model_name="telegramupdatelog",
            name="update_id",
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.AddConstraint(
            model_name="telegramupdatelog",
            constraint=models.UniqueConstraint(fields=["messenger_provider", "update_id"], name="unique_bot_update_provider_update"),
        ),
    ]
