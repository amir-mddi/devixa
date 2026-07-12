from django.db import migrations, models
from django.db.models import Count
from django.db.models.functions import Lower


def validate_case_insensitive_uniqueness(apps, schema_editor):
    User = apps.get_model("accounts", "CustomUser")

    duplicate_usernames = (
        User.objects.annotate(normalized=Lower("username"))
        .values("normalized")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .count()
    )
    duplicate_emails = (
        User.objects.exclude(email="")
        .annotate(normalized=Lower("email"))
        .values("normalized")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .count()
    )
    if duplicate_usernames or duplicate_emails:
        raise RuntimeError(
            "Cannot add case-insensitive account constraints: "
            f"duplicate username groups={duplicate_usernames}, "
            f"duplicate email groups={duplicate_emails}. Resolve duplicates first."
        )

    User.objects.filter(is_deleted=True, is_active=True).update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0011_alter_socialaccount_user_created_object_and_more")]

    operations = [
        migrations.RunPython(validate_case_insensitive_uniqueness, migrations.RunPython.noop),
        migrations.DeleteModel(name="TokenBlacklist"),
        migrations.AddConstraint(
            model_name="customuser",
            constraint=models.UniqueConstraint(
                Lower("username"),
                name="accounts_user_username_ci_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="customuser",
            constraint=models.UniqueConstraint(
                Lower("email"),
                condition=~models.Q(email=""),
                name="accounts_user_email_ci_unique",
            ),
        ),
    ]
