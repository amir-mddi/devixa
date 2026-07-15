from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from backend.apps.accounts.entities.oauth_entity import OAuthProfileEntity
from backend.apps.accounts.exceptions.oauth_exceptions import OAuthProviderError
from backend.apps.accounts.models import SocialAccount
from backend.apps.accounts.vo.oauth_vo import OAuthMessageVO, OAuthSafeProfileKeyVO

User = get_user_model()


class OAuthAccountRepository:
    @staticmethod
    def get_user_by_email(email: str):
        return User.objects.filter(email__iexact=email).first()

    @transaction.atomic
    def link_or_refresh(self, *, user, profile: OAuthProfileEntity) -> SocialAccount:
        existing_provider_account = (
            SocialAccount.objects.select_for_update()
            .select_related("user")
            .filter(provider=profile.provider, provider_user_id=profile.provider_user_id)
            .first()
        )
        if existing_provider_account and existing_provider_account.user_id != user.id:
            raise OAuthProviderError(OAuthMessageVO.ACCOUNT_LINK_CONFLICT.value)

        existing_user_provider = (
            SocialAccount.objects.select_for_update()
            .filter(user_id=user.id, provider=profile.provider)
            .first()
        )
        if existing_user_provider and existing_user_provider.provider_user_id != profile.provider_user_id:
            raise OAuthProviderError(OAuthMessageVO.PROVIDER_ALREADY_LINKED.value)

        safe_data = self._safe_profile_data(profile)
        account = existing_provider_account or existing_user_provider
        if account:
            changed_fields: list[str] = []
            if account.email != profile.email:
                account.email = profile.email
                changed_fields.append("email")
            if account.extra_data != safe_data:
                account.extra_data = safe_data
                changed_fields.append("extra_data")
            if not account.is_active:
                account.is_active = True
                changed_fields.append("is_active")
            if account.is_deleted:
                account.is_deleted = False
                account.deleted_at = None
                changed_fields.extend(["is_deleted", "deleted_at"])
            if changed_fields:
                account.save(update_fields=[*changed_fields, "updated_at"])
            return account

        try:
            return SocialAccount.objects.create(
                user=user,
                provider=profile.provider,
                provider_user_id=profile.provider_user_id,
                email=profile.email,
                extra_data=safe_data,
            )
        except IntegrityError as exc:
            raise OAuthProviderError(OAuthMessageVO.ACCOUNT_LINK_CONFLICT.value) from exc

    @staticmethod
    def _safe_profile_data(profile: OAuthProfileEntity) -> dict:
        allowed_keys = {item.value for item in OAuthSafeProfileKeyVO}
        return {key: value for key, value in profile.raw.items() if key in allowed_keys}
