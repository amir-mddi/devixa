import os
import subprocess
from datetime import datetime
from pathlib import Path

from celery import shared_task
from django.conf import settings

from backend.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


class BackupTaskConfig:
    def __init__(self):
        self.current_date = datetime.now()
        self.backup_file_name = self.current_date.strftime("%Y%m%d%H%M%S")
        self.main_path_project = Path(settings.BASE_DIR)
        self.backup_path = (self.main_path_project / "postgresql_backup").resolve()
        database = settings.DATABASES["default"]
        self.db_host = str(database.get("HOST") or "localhost")
        self.db_port = str(database.get("PORT") or "5432")
        self.db_password = str(database.get("PASSWORD") or "")
        self.db_user = str(database.get("USER") or "")
        self.db_name = str(database.get("NAME") or "")

    def validate(self) -> None:
        if not self.db_user or not self.db_name:
            raise RuntimeError("PostgreSQL backup credentials are incomplete.")


@shared_task
def backup_postgresql_of_each_day():
    config = BackupTaskConfig()
    config.validate()
    config.backup_path.mkdir(parents=True, exist_ok=True, mode=0o700)

    backup_files = sorted(
        (path for path in config.backup_path.iterdir() if path.is_file()),
        key=lambda path: path.stat().st_mtime,
    )
    for old_file in backup_files[:-2]:
        old_file.unlink(missing_ok=True)

    backup_file_path = config.backup_path / f"{config.backup_file_name}.dump"
    command = [
        "pg_dump",
        "--format=custom",
        "--no-password",
        "--host", config.db_host,
        "--port", config.db_port,
        "--username", config.db_user,
        "--file", str(backup_file_path),
        config.db_name,
    ]
    env = {**os.environ, "PGPASSWORD": config.db_password}
    try:
        subprocess.run(
            command,
            check=True,
            cwd=config.main_path_project,
            env=env,
            timeout=int(os.environ.get("POSTGRES_BACKUP_TIMEOUT_SECONDS", "1800")),
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        logger.exception("PostgreSQL backup failed.")
        raise

    if os.environ.get("POSTGRES_BACKUP_REMOTE_PATH", "").strip():
        transfer_backup_to_remote.delay(str(backup_file_path))
    return str(backup_file_path)


@shared_task
def transfer_backup_to_remote(backup_file_path: str):
    config = BackupTaskConfig()
    candidate = Path(backup_file_path).resolve()
    if candidate.parent != config.backup_path or not candidate.is_file():
        raise ValueError("Backup path is outside the configured backup directory.")

    remote_path = os.environ.get("POSTGRES_BACKUP_REMOTE_PATH", "").strip()
    if not remote_path:
        return "Remote backup transfer is disabled."

    try:
        subprocess.run(
            ["rsync", "-avz", "--", str(candidate), remote_path],
            check=True,
            timeout=int(os.environ.get("POSTGRES_BACKUP_TRANSFER_TIMEOUT_SECONDS", "1800")),
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        logger.exception("PostgreSQL backup transfer failed.")
        raise
    return "Backup successfully transferred."
