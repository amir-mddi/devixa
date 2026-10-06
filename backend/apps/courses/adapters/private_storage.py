from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateCourseFileStorage(FileSystemStorage):
    """Filesystem storage intentionally outside MEDIA_ROOT.

    Files stored here have no public media URL. They are served only through
    LMS download views after the domain access policy approves the request.
    """

    def __init__(self):
        location = Path(
            getattr(
                settings,
                "COURSE_PRIVATE_MEDIA_ROOT",
                Path(settings.BASE_DIR) / "private_media" / "courses",
            )
        )
        super().__init__(location=location, base_url=None)

    def url(self, name):
        raise ValueError("Private course files do not expose direct URLs.")


def get_private_course_storage():
    return PrivateCourseFileStorage()
