from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from PIL import Image
from rest_framework.exceptions import ValidationError

from backend.apps.common.helpers.validators.security_validators import (
    validate_course_thumbnail,
    validate_payment_receipt_file,
)
from backend.apps.core_models.constants.runtime_config import RuntimeConfig


def _png_file(*, width=2, height=2, name="image.png"):
    stream = BytesIO()
    Image.new("RGB", (width, height)).save(stream, format="PNG")
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


class UploadedFileSecurityValidatorTests(SimpleTestCase):
    def test_valid_image_content_passes_receipt_validation(self):
        upload = _png_file(name="receipt.png")

        self.assertIs(validate_payment_receipt_file(upload), upload)

    def test_signature_only_file_is_rejected_as_malformed_image(self):
        upload = SimpleUploadedFile(
            "receipt.png",
            b"\x89PNG\r\n\x1a\nnot-an-image",
            content_type="image/png",
        )

        with self.assertRaises(ValidationError):
            validate_payment_receipt_file(upload)

    @override_settings(COURSE_THUMBNAIL_MAX_PIXELS=4)
    def test_image_pixel_limit_is_enforced(self):
        with self.assertRaises(ValidationError):
            validate_course_thumbnail(_png_file(width=3, height=3))


class RuntimeSecretGenerationTests(SimpleTestCase):
    def test_temporary_password_has_secure_minimum_length_and_mixed_classes(self):
        password = RuntimeConfig().generate_random_password()

        self.assertEqual(len(password), 12)
        self.assertTrue(any(character.isalpha() for character in password))
        self.assertGreaterEqual(sum(character.isdigit() for character in password), 3)

    def test_verification_code_is_exactly_six_digits(self):
        code = RuntimeConfig().generate_verification_code()

        self.assertRegex(code, r"^\d{6}$")
