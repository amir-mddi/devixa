from __future__ import annotations

import secrets

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from backend.apps.referrals.dtos import ReferralApplyDTO, ReferralSummaryDTO
from backend.apps.referrals.entities import ReferralInviteEntity
from backend.apps.referrals.repositories import ReferralRepository
from backend.apps.referrals.value_objects import ReferralLimitVO, ReferralMessageVO, ReferralVO


class ReferralLogic:
    def __init__(self, repository: ReferralRepository | None = None):
        self.repository = repository or ReferralRepository()

    @staticmethod
    def normalize_code(code: str | None) -> str:
        return "".join((code or "").strip().upper().split())

    def is_valid_code(self, code: str | None) -> bool:
        normalized = self.normalize_code(code)
        return bool(normalized and self.repository.find_code(normalized))

    def resolve_code(self, code: str | None):
        normalized = self.normalize_code(code)
        if not normalized:
            return None
        record = self.repository.find_code(normalized)
        if record is None:
            raise ValidationError(ReferralMessageVO.INVALID_CODE.value)
        return record

    @transaction.atomic
    def apply(self, dto: ReferralApplyDTO):
        record = self.resolve_code(dto.code)
        if record is None:
            return None
        if record.user_id == dto.invitee.id:
            raise ValidationError(ReferralMessageVO.SELF_REFERRAL.value)
        if self.repository.invite_exists_for_user(dto.invitee):
            raise ValidationError(ReferralMessageVO.ALREADY_REFERRED.value)
        return self.repository.create_invite(
            inviter=record.user,
            invitee=dto.invitee,
            referral_code=record,
        )

    def get_or_create_code(self, user) -> str:
        existing = self.repository.get_code_record(user)
        if existing:
            return existing.code

        for _ in range(ReferralLimitVO.GENERATION_ATTEMPTS.value):
            random_part = "".join(
                secrets.choice(ReferralVO.CODE_ALPHABET.value)
                for _ in range(ReferralLimitVO.CODE_RANDOM_LENGTH.value)
            )
            candidate = f"{ReferralVO.CODE_PREFIX.value}{random_part}"
            try:
                return self.repository.create_code(user=user, code=candidate).code
            except IntegrityError:
                existing = self.repository.get_code_record(user)
                if existing:
                    return existing.code
                continue
        raise RuntimeError("Could not generate a unique referral code.")

    def summary(self, user) -> ReferralSummaryDTO:
        code = self.get_or_create_code(user)
        recent = self.repository.recent_invites(user, limit=ReferralLimitVO.RECENT_INVITEES.value)
        return ReferralSummaryDTO(
            code=code,
            invited_count=self.repository.count_invites(user),
            recent_invitees=tuple(
                ReferralInviteEntity(
                    username=item.invitee.username,
                    full_name=item.invitee.get_full_name().strip(),
                    registered_at=item.registered_at,
                )
                for item in recent
            ),
        )
