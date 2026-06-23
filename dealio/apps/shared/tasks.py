import os
import subprocess
from datetime import datetime

from celery.app import shared_task
from django.conf import settings


class BackupTaskConfig:
    def __init__(self):
        self.current_date = datetime.now()
        self.backup_file_name = self.current_date.strftime("%Y%m%d%H%M%S")
        self.current_path = os.getcwd()
        self.main_path_project = self.current_path.removesuffix('/accounts')
        self.backup_path = os.path.join(self.main_path_project, "postgresql_backup")
        self.db_host = settings.DATABASES['default'].get('HOST', 'localhost')
        self.db_password = settings.DATABASES['default'].get('PASSWORD')
        self.db_user = settings.DATABASES['default'].get('USER')
        self.db_name = settings.DATABASES['default'].get('NAME')


@shared_task
def backup_postgresql_of_each_day():
    config = BackupTaskConfig()

    os.makedirs(os.path.join(config.main_path_project, "postgresql_backup"), exist_ok=True)

    backup_files = os.listdir(config.backup_path)

    if len(backup_files) >= 3:
        oldest_file = sorted(backup_files)[0]
        os.remove(os.path.join(config.backup_path, oldest_file))
    backup_file_path = os.path.join(config.backup_path, config.backup_file_name)
    command = f"PGPASSWORD={config.db_password} pg_dump -U {config.db_user} -d {config.db_name} -h {config.db_host} > {backup_file_path}.dump"
    try:
        subprocess.run(command, shell=True, check=True, cwd=config.main_path_project)
        transfer_backup_to_remote.delay(backup_file_path)
    except subprocess.CalledProcessError as e:
        print(f"Error running backup command: {e}")


@shared_task
def transfer_backup_to_remote(backup_file_path):
    remote_path = "root@172.16.16.49:/mnt/data/backend_web/postgresql_backup/"
    rsync_command = f"rsync -avz {backup_file_path} {remote_path}"

    try:
        subprocess.run(rsync_command, shell=True, check=True)
        return "Backup successfully transferred."
    except subprocess.CalledProcessError as e:
        return f"Error transferring backup: {e}"
