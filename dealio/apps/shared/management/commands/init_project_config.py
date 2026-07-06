from django.core.management import BaseCommand

from dealio.apps.shared.initial_data.initial_data.project_config_initial import initialize_project_config


class Command(BaseCommand):
    help = "Initialize project config from environment only if the database object does not exist."

    def handle(self, *args, **options):
        project_config, created = initialize_project_config()

        if not project_config:
            self.stdout.write(self.style.ERROR("Project config could not be initialized. Run migrations first."))
            return

        if created:
            self.stdout.write(self.style.SUCCESS("Project config initialized from environment."))
            return

        self.stdout.write(self.style.WARNING("Project config already exists; environment values ignored."))
