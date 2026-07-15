from backend.apps.accounts.models import Access, Role
from backend.apps.shared.initial_data.initial_data.role_initilizer_data import InitializerData


def create_role_access_base():
    for sample in InitializerData.role_data:
        access_instances = []

        for access_name in sample.get("accesses", []):
            access_instance, _ = Access.objects.get_or_create(name=access_name)
            access_instances.append(access_instance)

        role, _ = Role.objects.update_or_create(
            symbol=sample["symbol"],
            defaults={
                "name": sample["name"],
            },
        )

        role.accesses.set(access_instances)
        role.save()