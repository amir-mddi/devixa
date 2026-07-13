from __future__ import annotations

from django.test import TestCase, override_settings

from dealio.apps.accounts.adapters.oauth_provider_adapter import BaseOAuthProviderAdapter
from dealio.apps.accounts.dtos.oauth_dto import (
    OAuthAuthorizationRequestDTO,
    OAuthCodeExchangeDTO,
)
from dealio.apps.accounts.entities.oauth_entity import OAuthProfileEntity
from dealio.apps.accounts.enums.oauth_enums import OAuthProviderEnum
from dealio.apps.accounts.exceptions.oauth_exceptions import OAuthProviderError
from dealio.apps.accounts.logic.oauth_logic import OAuthLoginLogic
from dealio.apps.accounts.models import SocialAccount
from dealio.apps.accounts.vo.oauth_vo import OAuthMessageVO
from dealio.tests.factories import UserFactory


class StubOAuthProviderAdapter(BaseOAuthProviderAdapter):
    provider = OAuthProviderEnum.GOOGLE

    def __init__(self, profile: OAuthProfileEntity):
        self.profile = profile

    def build_authorization_url(self, dto: OAuthAuthorizationRequestDTO) -> str:
        return f"https://provider.example/authorize?state={dto.state}"

    def exchange_code(self, dto: OAuthCodeExchangeDTO) -> OAuthProfileEntity:
        return self.profile


@override_settings(
    OAUTH_ALLOWED_REDIRECT_URIS=["https://frontend.example/oauth/callback"],
)
class OAuthLoginLogicTests(TestCase):
    redirect_uri = "https://frontend.example/oauth/callback"

    def _profile(self, **overrides) -> OAuthProfileEntity:
        values = {
            "provider": OAuthProviderEnum.GOOGLE.value,
            "provider_user_id": "google-user-123",
            "email": "existing@gmail.com",
            "email_verified": True,
            "username_hint": "existing",
            "first_name": "Ali",
            "last_name": "Rezai",
            "raw": {
                "sub": "google-user-123",
                "picture": "https://images.example/avatar.png",
                "email": "must-not-be-persisted-in-extra-data@example.com",
                "access_token": "must-never-be-persisted",
            },
        }
        values.update(overrides)
        return OAuthProfileEntity(**values)

    def _logic(self, profile: OAuthProfileEntity) -> OAuthLoginLogic:
        return OAuthLoginLogic(
            provider_adapters={
                OAuthProviderEnum.GOOGLE.value: StubOAuthProviderAdapter(profile),
            }
        )

    def _dto(self) -> OAuthCodeExchangeDTO:
        return OAuthCodeExchangeDTO(
            provider=OAuthProviderEnum.GOOGLE.value,
            code="valid-code",
            redirect_uri=self.redirect_uri,
        )

    def test_provider_verified_flag_does_not_treat_false_string_as_true(self):
        self.assertFalse(StubOAuthProviderAdapter._is_verified("false"))
        self.assertTrue(StubOAuthProviderAdapter._is_verified("true"))

    def test_existing_user_is_authenticated_and_provider_link_is_created(self):
        user = UserFactory.create(email="existing@gmail.com")

        result = self._logic(self._profile()).authenticate(self._dto())

        self.assertEqual(result.user, user)
        social_account = SocialAccount.objects.get(user=user)
        self.assertEqual(social_account.provider, OAuthProviderEnum.GOOGLE.value)
        self.assertEqual(social_account.provider_user_id, "google-user-123")
        self.assertEqual(
            social_account.extra_data,
            {
                "sub": "google-user-123",
                "picture": "https://images.example/avatar.png",
            },
        )

    def test_user_is_never_created_when_provider_email_is_not_registered(self):
        with self.assertRaisesMessage(
            OAuthProviderError,
            OAuthMessageVO.ACCOUNT_NOT_REGISTERED.value,
        ):
            self._logic(self._profile(email="missing@gmail.com")).authenticate(self._dto())

        self.assertFalse(SocialAccount.objects.exists())

    def test_unverified_provider_email_is_rejected(self):
        UserFactory.create(email="existing@gmail.com")

        with self.assertRaisesMessage(
            OAuthProviderError,
            OAuthMessageVO.UNVERIFIED_EMAIL.value,
        ):
            self._logic(self._profile(email_verified=False)).authenticate(self._dto())

        self.assertFalse(SocialAccount.objects.exists())

    def test_inactive_local_user_is_rejected(self):
        UserFactory.create(email="existing@gmail.com", is_active=False)

        with self.assertRaisesMessage(
            OAuthProviderError,
            OAuthMessageVO.ACCOUNT_INACTIVE.value,
        ):
            self._logic(self._profile()).authenticate(self._dto())

    def test_provider_identity_cannot_be_linked_to_another_local_user(self):
        first_user = UserFactory.create(email="first@gmail.com")
        UserFactory.create(email="existing@gmail.com")
        SocialAccount.objects.create(
            user=first_user,
            provider=OAuthProviderEnum.GOOGLE.value,
            provider_user_id="google-user-123",
        )

        with self.assertRaisesMessage(
            OAuthProviderError,
            OAuthMessageVO.ACCOUNT_LINK_CONFLICT.value,
        ):
            self._logic(self._profile()).authenticate(self._dto())

    @override_settings(OAUTH_ALLOWED_REDIRECT_URIS=[])
    def test_redirect_allowlist_is_required_even_in_debug(self):
        with self.assertRaisesMessage(
            OAuthProviderError,
            OAuthMessageVO.REDIRECT_ALLOWLIST_MISSING.value,
        ):
            self._logic(self._profile()).authenticate(self._dto())

    def test_redirect_uri_must_match_allowlist_exactly(self):
        dto = OAuthCodeExchangeDTO(
            provider=OAuthProviderEnum.GOOGLE.value,
            code="valid-code",
            redirect_uri="https://evil.example/oauth/callback",
        )

        with self.assertRaisesMessage(
            OAuthProviderError,
            OAuthMessageVO.REDIRECT_NOT_ALLOWED.value,
        ):
            self._logic(self._profile()).authenticate(dto)
