import re
from django.core.validators import RegexValidator
from rest_framework import serializers

from dealio.apps.shared.models import ApiKeyManagerModel, ProjectConfigModel
from dealio.apps.shared.vo.project_config_vo import ProjectConfigSerializerMessageVO
from dealio.apps.common.utils.network_security import UnsafeOutboundUrlError, validate_public_https_url


class CommonSerializerField:
    phone_number = serializers.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r"^09[0-9]{9}$",
                message="Phone number must be digits and start with 09.........",
                code="invalid_phone_number",
            )
        ],
    )


class BaseResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    en_msg = serializers.CharField()
    fa_msg = serializers.CharField()
    code = serializers.IntegerField()
    status = serializers.CharField()
    data = serializers.DictField(allow_null=True)


class ListResponseSerializer(BaseResponseSerializer):
    data = serializers.ListField(child=serializers.DictField(), allow_null=True)


class BaseSerializerModel(serializers.ModelSerializer):
    user_created_object = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_updated_object = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        abstract = True
        base_fields = [
            "id",
            "is_active",
            "created_at",
            "updated_at",
            "deleted_at",
            "user_created_object",
            "user_updated_object",
        ]
        base_read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "is_active"
        )

    # def to_internal_value(self, data):
    #     for key, value in data.items():
    #         if isinstance(value, UUID):
    #             data[key] = str(value)
    #     return data

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        meta = getattr(cls, "Meta", None)
        if meta:
            child_fields = list(getattr(meta, "fields", []))
            base_fields = list(getattr(BaseSerializerModel.Meta, "base_fields", []))
            meta.fields = tuple(child_fields + [f for f in base_fields if f not in child_fields])

            child_read_only_fields = list(getattr(meta, "read_only_fields", []))
            base_read_only_fields = list(getattr(BaseSerializerModel.Meta, "base_read_only_fields", []))
            meta.read_only_fields = tuple(
                child_read_only_fields
                + [
                    field
                    for field in base_read_only_fields
                    if field not in child_read_only_fields
                ]
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        for field_name in ["created_at", "updated_at", "deleted_at", "is_active"]:
            if field_name in self.fields:
                self.fields[field_name].read_only = True
        if request and request.method == "POST":
            self.fields.pop("is_active", None)
        # if "is_active" in self.fields and request:
        #     if not getattr(request.user.role, "name", None) == UserRoleVO.ADMIN:
        #         self.fields.pop("is_active")
        #         self.fields["is_active"].read_only = True

    # def validate(self, attrs):
    #     attrs = super().validate(attrs)
    #     request = self.context.get("request")
    #     if request and request.method == "POST":
    #         attrs.pop("is_active", None)
    #
    #     return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user_created_object"] = request.user
            validated_data["user_updated_object"] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user_updated_object"] = request.user
        return super().update(instance, validated_data)


class ApiKeyMngSerializer(BaseSerializerModel):
    api_key = serializers.CharField(write_only=True, min_length=32, max_length=255)
    masked_api_key = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseSerializerModel.Meta):
        model = ApiKeyManagerModel
        fields = ["api_key", "masked_api_key", "status"]

    @staticmethod
    def get_masked_api_key(obj):
        value = str(obj.api_key or "")
        return f"{value[:4]}...{value[-4:]}" if len(value) >= 12 else "***"


class ProjectConfigSerializer(BaseSerializerModel):
    class Meta(BaseSerializerModel.Meta):
        model = ProjectConfigModel
        fields = [
            "name",
            "display_name",
            "slug",
            "description",
            "tagline",
            "email_domain",
            "contact_email",
            "support_email",
            "sales_email",
            "partnership_email",
            "github_url",
            "linkedin_url",
            "telegram_url",
            "instagram_url",
            "telegram_bot_url",
            "bale_bot_url",
            "phone",
            "address",
            "working_hours",
        ]
        read_only_fields = BaseSerializerModel.Meta.base_read_only_fields

    def validate_slug(self, value: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", value or ""):
            raise serializers.ValidationError(ProjectConfigSerializerMessageVO.SLUG_INVALID.value)
        return value.lower()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        url_fields = (
            "github_url",
            "linkedin_url",
            "telegram_url",
            "instagram_url",
            "telegram_bot_url",
            "bale_bot_url",
        )
        for field_name in url_fields:
            value = str(attrs.get(field_name, "") or "").strip()
            if not value:
                continue
            try:
                attrs[field_name] = validate_public_https_url(value, resolve_dns=False)
            except UnsafeOutboundUrlError as exc:
                raise serializers.ValidationError({field_name: str(exc)}) from exc
        return attrs
