from django.core.management import BaseCommand


from dealio.apps.shared.initial_data.initial_data.role_initial import create_role_access_base


class Command(BaseCommand):
    help = "generate sample data for test db"

    def handle(self, *args, **options):
        create_role_access_base()