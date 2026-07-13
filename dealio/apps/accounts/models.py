from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from dealio.apps.core_models.entities.base.base import BaseModel


def profile_photo_upload_to(instance, filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"accounts/profile/{instance.id}/{uuid4().hex}.{extension}"


class Access(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name}"


class Role(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    accesses = models.ManyToManyField(
        "Access", related_name="access_roles", null=False, default=None
    )
    symbol = models.CharField(max_length=20, unique=True, null=True)

    def __str__(self):
        return f"{self.name}"


class CustomUser(BaseModel, AbstractUser):
    phone_number = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex="^09[0-9]{9}$",
                message="phone number must be digit and start with 09.........",
                code="invalid_phone_number",
            ),
        ],
        unique=True,
        null=True,
        blank=True,
        help_text="Phone can be collected after social signup.",
    )
    role = models.ForeignKey(Role, related_name="user_role", on_delete=models.PROTECT)
    email_verified = models.BooleanField(default=False)
    phone_number_verified = models.BooleanField(default=False)
    is_service_user = models.BooleanField(default=False)
    profile_photo = models.ImageField(
        upload_to=profile_photo_upload_to,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        self.email = str(self.email or "").strip().lower()
        self.username = str(self.username or "").strip()

        if not self._state.adding:
            previous = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("phone_number", "email")
                .first()
                or {}
            )
            changed_verification_fields = set()
            if previous.get("phone_number") != self.phone_number:
                self.phone_number_verified = False
                changed_verification_fields.add("phone_number_verified")
            if str(previous.get("email") or "").strip().lower() != self.email:
                self.email_verified = False
                changed_verification_fields.add("email_verified")

            update_fields = kwargs.get("update_fields")
            if update_fields is not None and changed_verification_fields:
                kwargs["update_fields"] = (
                    set(update_fields) | changed_verification_fields | {"email"}
                )

        super().save(*args, **kwargs)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("username"),
                name="accounts_user_username_ci_unique",
            ),
            models.UniqueConstraint(
                Lower("email"),
                condition=~Q(email=""),
                name="accounts_user_email_ci_unique",
            ),
        ]

    # def save(self, *args, **kwargs):
    #     try:
    #         role = Role.objects.get(symbol="user")
    #     except Role.DoesNotExist:
    #         raise Exception("Role Not Found")
    #     self.role = role
    #     super().save(*args, **kwargs)


class SocialAuthProvider(models.TextChoices):
    GOOGLE = "google", "Google"
    GITHUB = "github", "GitHub"


class SocialAccount(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="social_accounts",
        on_delete=models.CASCADE,
    )
    provider = models.CharField(
        max_length=20,
        choices=SocialAuthProvider.choices,
        db_index=True,
    )
    provider_user_id = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_user_id"],
                name="unique_social_provider_user_id",
            ),
            models.UniqueConstraint(
                fields=["user", "provider"],
                name="unique_social_user_provider",
            ),
        ]
        indexes = [
            models.Index(
                fields=["provider", "email"], name="social_provider_email_idx"
            ),
        ]

    def __str__(self):
        return f"{self.provider}:{self.provider_user_id}"
