from django.core.management import BaseCommand


from backend.apps.shared.initial_data.initial_data.role_initial import create_role_access_base
from backend.apps.shared.initial_data.initial_data.project_config_initial import initialize_project_config


class Command(BaseCommand):
    help = "generate sample data for test db"

    def handle(self, *args, **options):
        create_role_access_base()
        _, created = initialize_project_config()
        if created:
            self.stdout.write(self.style.SUCCESS("Project config initialized from environment."))
        else:
            self.stdout.write(self.style.WARNING("Project config already exists; environment values ignored."))
