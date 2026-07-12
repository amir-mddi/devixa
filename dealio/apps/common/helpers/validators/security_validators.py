from __future__ import annotations

from pathlib import Path
import warnings

from PIL import Image, UnidentifiedImageError

from django.conf import settings
from rest_framework import serializers

from dealio.apps.common.utils.network_security import (
    UnsafeOutboundUrlError,
    validate_public_https_url,
)


_ALLOWED_RECEIPT_TYPES = {
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".pdf": ("application/pdf", b"%PDF-"),
}


def _validate_image_content(uploaded_file, *, max_pixels: int, invalid_message: str) -> None:
    try:
        position = uploaded_file.tell()
        uploaded_file.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(uploaded_file) as image:
                width, height = image.size
                if width <= 0 or height <= 0 or width * height > max_pixels:
                    raise serializers.ValidationError(invalid_message)
                image.verify()
        uploaded_file.seek(position)
    except serializers.ValidationError:
        try:
            uploaded_file.seek(position)
        except (AttributeError, OSError, UnboundLocalError):
            pass
        raise
    except (
        AttributeError,
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        try:
            uploaded_file.seek(position)
        except (AttributeError, OSError, UnboundLocalError):
            pass
        raise serializers.ValidationError(invalid_message) from exc


def validate_payment_receipt_file(uploaded_file):
    max_bytes = int(getattr(settings, "PAYMENT_RECEIPT_MAX_BYTES", 5 * 1024 * 1024))
    if uploaded_file.size > max_bytes:
        raise serializers.ValidationError(
            f"Receipt file must be at most {max_bytes // (1024 * 1024)} MB."
        )

    extension = Path(uploaded_file.name or "").suffix.lower()
    expected = _ALLOWED_RECEIPT_TYPES.get(extension)
    if not expected:
        raise serializers.ValidationError("Only JPG, PNG, and PDF receipts are allowed.")

    expected_content_type, signature = expected
    content_type = str(getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and content_type != expected_content_type:
        raise serializers.ValidationError("Receipt file type does not match its extension.")

    try:
        position = uploaded_file.tell()
        header = uploaded_file.read(max(len(item[1]) for item in _ALLOWED_RECEIPT_TYPES.values()))
        uploaded_file.seek(position)
    except (AttributeError, OSError):
        raise serializers.ValidationError("Receipt file could not be validated.")

    if not header.startswith(signature):
        raise serializers.ValidationError("Receipt file content is invalid.")
    if extension != ".pdf":
        _validate_image_content(
            uploaded_file,
            max_pixels=int(getattr(settings, "PAYMENT_RECEIPT_MAX_PIXELS", 40_000_000)),
            invalid_message="Receipt image content is invalid.",
        )
    return uploaded_file


def validate_safe_https_url(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        return validate_public_https_url(value, resolve_dns=False)
    except UnsafeOutboundUrlError as exc:
        raise serializers.ValidationError(str(exc)) from exc


def validate_course_thumbnail(uploaded_file):
    max_bytes = int(getattr(settings, "COURSE_THUMBNAIL_MAX_BYTES", 3 * 1024 * 1024))
    if uploaded_file.size > max_bytes:
        raise serializers.ValidationError(
            f"Thumbnail must be at most {max_bytes // (1024 * 1024)} MB."
        )
    extension = Path(uploaded_file.name or "").suffix.lower()
    signatures = {
        ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
        ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
        ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
        ".webp": ("image/webp", b"RIFF"),
    }
    expected = signatures.get(extension)
    if not expected:
        raise serializers.ValidationError("Only JPG, PNG, and WebP thumbnails are allowed.")
    expected_type, signature = expected
    content_type = str(getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and content_type != expected_type:
        raise serializers.ValidationError("Thumbnail type does not match its extension.")
    try:
        position = uploaded_file.tell()
        header = uploaded_file.read(12)
        uploaded_file.seek(position)
    except (AttributeError, OSError):
        raise serializers.ValidationError("Thumbnail could not be validated.")
    if not header.startswith(signature):
        raise serializers.ValidationError("Thumbnail content is invalid.")
    if extension == ".webp" and header[8:12] != b"WEBP":
        raise serializers.ValidationError("Thumbnail content is invalid.")
    _validate_image_content(
        uploaded_file,
        max_pixels=int(getattr(settings, "COURSE_THUMBNAIL_MAX_PIXELS", 25_000_000)),
        invalid_message="Thumbnail content is invalid.",
    )
    return uploaded_file
