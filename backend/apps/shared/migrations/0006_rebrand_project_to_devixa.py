from django.db import migrations


PROJECT_SINGLETON_KEY = "default"
DEVIXA_NAME = "devixa"
DEVIXA_DISPLAY_NAME = "Devixa"
DEVIXA_SLUG = "devixa"
DEVIXA_EMAIL_DOMAIN = "acdevixa.ir"


def apply_devixa_branding(apps, schema_editor):
    project_config_model = apps.get_model("shared", "ProjectConfigModel")
    project_config_model.objects.filter(
        singleton_key=PROJECT_SINGLETON_KEY,
    ).update(
        name=DEVIXA_NAME,
        display_name=DEVIXA_DISPLAY_NAME,
        slug=DEVIXA_SLUG,
        email_domain=DEVIXA_EMAIL_DOMAIN,
    )


def reverse_devixa_branding(apps, schema_editor):
    # Branding migrations are intentionally not reversed because restoring an
    # obsolete public identity during rollback is unsafe and surprising.
    return None


class Migration(migrations.Migration):
    dependencies = [("shared", "0005_projectconfig_rubika_bot_url")]

    operations = [
        migrations.RunPython(
            apply_devixa_branding,
            reverse_code=reverse_devixa_branding,
        ),
    ]
