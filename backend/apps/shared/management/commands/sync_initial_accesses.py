# from django.conf import settings
# from django.core.management.base import BaseCommand
# from django.db import transaction
#
# from backend.apps.accounts.models import Access, Role
# from backend.apps.shared.initial_data.initial_data.intial_access import InitialAccessCache
# from backend.apps.shared.initial_data.initial_data.role_initilizer_data import InitializerData
#
#
# class Command(BaseCommand):
#     help = "Sync initial Access and Role data into database."
#
#     def add_arguments(self, parser):
#         parser.add_argument(
#             "--check-role",
#             default="admin",
#             help="Role symbol to check in InitializerData.role_data.",
#         )
#         parser.add_argument(
#             "--check-access",
#             default="LogoutView|post|any",
#             help="Access name to check and sync.",
#         )
#
#     @transaction.atomic
#     def handle(self, *args, **options):
#         check_role = options["check_role"]
#         check_access = options["check_access"]
#
#         access_names = [item["name"] for item in AccessData.access_list]
#         access_name_set = set(access_names)
#
#         role_by_symbol = {
#             item["symbol"]: item
#             for item in InitializerData.role_data
#         }
#
#         if check_access in access_name_set:
#             self.stdout.write(
#                 self.style.SUCCESS(
#                     f"AccessData has access: {check_access}"
#                 )
#             )
#         else:
#             self.stdout.write(
#                 self.style.WARNING(
#                     f"AccessData does not have access: {check_access}"
#                 )
#             )
#
#         role_data = role_by_symbol.get(check_role)
#
#         if role_data and check_access in role_data.get("accesses", []):
#             self.stdout.write(
#                 self.style.SUCCESS(
#                     f"Role '{check_role}' has access in role data: {check_access}"
#                 )
#             )
#         else:
#             self.stdout.write(
#                 self.style.WARNING(
#                     f"Role '{check_role}' does not have access in role data: {check_access}"
#                 )
#             )
#
#         created_access_count = 0
#
#         for access_name in access_names:
#             _, created = Access.objects.get_or_create(name=access_name)
#             created_access_count += int(created)
#
#         created_role_count = 0
#
#         for item in InitializerData.role_data:
#             role, created = Role.objects.update_or_create(
#                 symbol=item["symbol"],
#                 defaults={
#                     "name": item["name"],
#                 },
#             )
#
#             created_role_count += int(created)
#
#             role_accesses = []
#
#             for access_name in item.get("accesses", []):
#                 access, _ = Access.objects.get_or_create(name=access_name)
#                 role_accesses.append(access)
#
#             role.accesses.set(role_accesses)
#
#         settings.PERMISSIONS = InitialAccessCache.initial_accesses()
#
#         self.stdout.write(
#             self.style.SUCCESS(
#                 "Sync complete. "
#                 f"Created {created_access_count} accesses, "
#                 f"created {created_role_count} roles, "
#                 f"loaded {len(settings.PERMISSIONS)} permission patterns from DB."
#             )
#         )