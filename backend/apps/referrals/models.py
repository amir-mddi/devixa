from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.timezone import now

from backend.apps.core_models.entities.base.base import BaseModel


class ReferralCode(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="referral_code_record",
        on_delete=models.CASCADE,
    )
    code = models.CharField(max_length=16, unique=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["code", "is_active", "is_deleted"], name="referral_code_active_idx")]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.code}"


class ReferralInvite(BaseModel):
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="referral_invites_sent",
        on_delete=models.PROTECT,
    )
    invitee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="referral_invite_received",
        on_delete=models.CASCADE,
    )
    referral_code = models.ForeignKey(
        ReferralCode,
        related_name="invites",
        on_delete=models.PROTECT,
    )
    registered_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ["-registered_at"]
        constraints = [
            models.CheckConstraint(condition=~Q(inviter=F("invitee")), name="referral_inviter_not_invitee"),
        ]
        indexes = [
            models.Index(fields=["inviter", "registered_at"], name="referral_inviter_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.inviter_id}->{self.invitee_id}"
