from django.db import migrations


def create_instructor_role(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    role = Role.objects.filter(symbol="instructor").first()
    if role is None:
        role = Role.objects.filter(name="مدرس").first()
    if role is None:
        Role.objects.create(name="مدرس", symbol="instructor")
        return

    changed_fields = []
    if role.name != "مدرس":
        role.name = "مدرس"
        changed_fields.append("name")
    if role.symbol != "instructor":
        role.symbol = "instructor"
        changed_fields.append("symbol")
    if changed_fields:
        role.save(update_fields=changed_fields)


def remove_instructor_role(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    role = Role.objects.filter(symbol="instructor").first()
    if role and not role.user_role.exists():
        role.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_socialaccount_user_provider_unique"),
    ]

    operations = [
        migrations.RunPython(create_instructor_role, remove_instructor_role),
    ]
