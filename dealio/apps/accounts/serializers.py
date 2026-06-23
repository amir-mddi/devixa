from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from dealio.apps.accounts.models import Role
from dealio.apps.common.helpers.validators.account_validators import validate_iranian_phone_number, \
    validate_gmail_email, validate_persian_text, validate_english_username
from dealio.apps.shared.serializers import BaseSerializerModel

User = get_user_model()


class UserSerializer(BaseSerializerModel):
    role = serializers.SerializerMethodField()

    # role_id = serializers.PrimaryKeyRelatedField(
    #     source="role",
    #     queryset=Role.objects.all(),
    #     write_only=True,
    #     required=True,
    # )

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
        fields = ["last_login", "is_superuser", "username", "email", "is_staff", "date_joined", "phone_number",
                  "first_name", "last_name", "role"]
        read_only_fields = [
            "last_login",
            "is_superuser",
            "is_staff",
            "date_joined",
            "role"
        ]


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(write_only=True, required=True)
    newPassword = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )


class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True, required=True)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        user_role = user.role.symbol
        token["role"] = user_role

        return token

    # def validate(self, attrs):
    #     data = super().validate(attrs)
    #     is_admin = self.user.is_superuser or self.user.is_staff or self.user.groups.filter(name="Admin").exists()
    #     data["role"] = "admin" if is_admin else "user"  # only in the response JSON
    #     return data


class ForgotPasswordSendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, required=True)


class ForgotPasswordVerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, required=True)
    code = serializers.RegexField(
        regex=r"^\d{6}$",
        write_only=True,
        required=True,
        error_messages={"invalid": "Code must be a 6-digit number."},
    )
    newPassword = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )