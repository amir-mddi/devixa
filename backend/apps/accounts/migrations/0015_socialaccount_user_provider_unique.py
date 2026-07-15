from django.db import migrations, models
from django.db.models import Count


def deduplicate_user_provider_links(apps, schema_editor):
    SocialAccount = apps.get_model("accounts", "SocialAccount")
    duplicates = (
        SocialAccount.objects.values("user_id", "provider")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
    )
    for duplicate in duplicates.iterator():
        account_ids = list(
            SocialAccount.objects.filter(
                user_id=duplicate["user_id"],
                provider=duplicate["provider"],
            )
            .order_by("is_deleted", "-updated_at", "id")
            .values_list("id", flat=True)
        )
        SocialAccount.objects.filter(id__in=account_ids[1:]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0014_customuser_profile_photo"),
    ]

    operations = [
        migrations.RunPython(
            deduplicate_user_provider_links,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="socialaccount",
            constraint=models.UniqueConstraint(
                fields=("user", "provider"),
                name="unique_social_user_provider",
            ),
        ),
    ]
