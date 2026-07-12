from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from dealio.apps.common.helpers.validators.account_validators import (
    validate_english_username,
    validate_gmail_email,
    validate_iranian_phone_number,
    validate_persian_text,
)
from dealio.apps.shared.serializers import BaseSerializerModel

User = get_user_model()


class UserSerializer(BaseSerializerModel):
    role = serializers.SerializerMethodField()

    def validate_phone_number(self, value):
        return validate_iranian_phone_number(value)

    def validate_email(self, value):
        return validate_gmail_email(value)

    def validate_first_name(self, value):
        return validate_persian_text(value)

    def validate_last_name(self, value):
        return validate_persian_text(value)

    def validate_username(self, value):
        return validate_english_username(value)

    def get_role(self, obj):
        if not obj.role:
            return None

        return {
            "id": str(obj.role.id),
            "name": obj.role.name,
            "symbol": obj.role.symbol,
        }

    class Meta:
        model = User
        fields = [
            "last_login",
            "is_superuser",
            "username",
            "email",
            "is_staff",
            "date_joined",
            "phone_number",
            "first_name",
            "last_name",
            "role",
            "email_verified",
            "phone_number_verified",
        ]
        read_only_fields = [
            "last_login",
            "is_superuser",
            "is_staff",
            "date_joined",
            "role",
            "email_verified",
            "phone_number_verified",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )


class SixDigitCodeSerializer(serializers.Serializer):
    code = serializers.RegexField(
        regex=r"^\d{6}$",
        write_only=True,
        required=True,
        error_messages={"invalid": "Code must be a 6-digit number."},
    )


class VerifyCodeSerializer(SixDigitCodeSerializer):
    pass


class PhoneVerificationCodeSerializer(SixDigitCodeSerializer):
    pass


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role.symbol
        return token


class ForgotPasswordSendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, required=True)


class ForgotPasswordVerifyCodeSerializer(SixDigitCodeSerializer):
    email = serializers.EmailField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )


class ForgotPasswordSmsSendCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(write_only=True, required=True)

    def validate_phone_number(self, value):
        return validate_iranian_phone_number(value)


class ForgotPasswordSmsVerifyCodeSerializer(SixDigitCodeSerializer):
    phone_number = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )

    def validate_phone_number(self, value):
        return validate_iranian_phone_number(value)


class SocialOAuthLoginSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True, required=True, trim_whitespace=True)
    redirect_uri = serializers.URLField(write_only=True, required=True)

    def to_internal_value(self, data):
        if isinstance(data, dict) and "redirectUri" in data and "redirect_uri" not in data:
            data = {**data, "redirect_uri": data["redirectUri"]}
        return super().to_internal_value(data)
