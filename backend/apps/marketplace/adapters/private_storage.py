from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage

# Not under MEDIA_ROOT or STATIC_ROOT: must never be served by the public web server.
class PrivateResumeStorage(FileSystemStorage):
    """Prevent generating public URLs for confidential applicant files."""

    def url(self, name):
        raise ValueError("Private résumés do not have public URLs")


resume_storage = PrivateResumeStorage(
    location=Path(settings.BASE_DIR) / "deployment" / "private_uploads",
)
