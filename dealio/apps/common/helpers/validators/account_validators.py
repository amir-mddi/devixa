# users/validators.py

import re
from rest_framework import serializers


IRAN_MOBILE_PATTERN = r"^(09\d{9}|\+989\d{9}|989\d{9})$"
PERSIAN_TEXT_PATTERN = r"^[\u0600-\u06FF\s‌]+$"
USERNAME_PATTERN = r"^[A-Za-z][A-Za-z0-9_.-]*$"


def validate_iranian_phone_number(value):
    if not value:
        raise serializers.ValidationError("Phone number is required.")

    value = value.strip()

    if not re.fullmatch(IRAN_MOBILE_PATTERN, value):
        raise serializers.ValidationError(
            "Phone number must be a valid Iranian mobile number."
        )

    return value


def validate_gmail_email(value):
    if not value:
        raise serializers.ValidationError("Email is required.")

    value = value.lower().strip()

    serializers.EmailField().run_validation(value)

    if not value.endswith("@gmail.com"):
        raise serializers.ValidationError("Email must be a Gmail address.")

    return value


def validate_persian_text(value):
    if not value:
        raise serializers.ValidationError("This field is required.")

    value = value.strip()

    if not re.fullmatch(PERSIAN_TEXT_PATTERN, value):
        raise serializers.ValidationError(
            "This field must contain Persian letters only."
        )

    return value


def validate_english_username(value):
    if not value:
        raise serializers.ValidationError("Username is required.")

    value = value.strip()

    if not re.fullmatch(USERNAME_PATTERN, value):
        raise serializers.ValidationError(
            "Username must start with an English letter and contain only English letters, numbers, underscore, dot, or hyphen."
        )

    return value