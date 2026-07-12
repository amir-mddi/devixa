import json
from dealio.apps.common.utils.common_utils import CommonUtils
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.crypto import get_random_string
from rest_framework_simplejwt.tokens import RefreshToken

from dealio.apps.accounts.models import Role, SocialAccount, SocialAuthProvider

logger = CommonUtils.get_project_logger(__name__)
User = get_user_model()


class OAuthProviderError(Exception):
    def __init__(self, public_message: str, *, status_code: int = 400, log_message: str | None = None):
        self.public_message = public_message
        self.status_code = status_code
        self.log_message = log_message or public_message
        super().__init__(public_message)


@dataclass(frozen=True)
class OAuthProfile:
    provider: str
    provider_user_id: str
    email: str
    email_verified: bool
    username_hint: str
    first_name: str = ""
    last_name: str = ""
    raw: dict[str, Any] | None = None


class SocialOAuthService:
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"
    GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

    def login_with_google(self, *, code: str, redirect_uri: str) -> dict[str, Any]:
        self._validate_redirect_uri(redirect_uri)
        client_id = self._required_setting("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = self._required_setting("GOOGLE_OAUTH_CLIENT_SECRET")

        token_data = self._post_json(
            self.GOOGLE_TOKEN_URL,
            {
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        access_token = token_data.get("access_token")
        if not access_token:
            raise OAuthProviderError("Google did not return an access token.")

        userinfo = self._get_json(
            self.GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        email = (userinfo.get("email") or "").lower().strip()
        if not email:
            raise OAuthProviderError("Google account does not expose an email address.")

        profile = OAuthProfile(
            provider=SocialAuthProvider.GOOGLE,
            provider_user_id=str(userinfo.get("sub") or ""),
            email=email,
            email_verified=bool(userinfo.get("email_verified")),
            username_hint=email.split("@")[0],
            first_name=userinfo.get("given_name") or "",
            last_name=userinfo.get("family_name") or "",
            raw=userinfo,
        )
        return self._issue_tokens_for_profile(profile)

    def login_with_github(self, *, code: str, redirect_uri: str) -> dict[str, Any]:
        self._validate_redirect_uri(redirect_uri)
        client_id = self._required_setting("GITHUB_OAUTH_CLIENT_ID")
        client_secret = self._required_setting("GITHUB_OAUTH_CLIENT_SECRET")

        token_data = self._post_json(
            self.GITHUB_TOKEN_URL,
            {
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        access_token = token_data.get("access_token")
        if not access_token:
            raise OAuthProviderError("GitHub did not return an access token.")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        github_user = self._get_json(self.GITHUB_USER_URL, headers=headers)
        email, verified = self._resolve_github_email(github_user=github_user, headers=headers)

        login = github_user.get("login") or email.split("@")[0]
        first_name, last_name = self._split_name(github_user.get("name") or "")
        profile = OAuthProfile(
            provider=SocialAuthProvider.GITHUB,
            provider_user_id=str(github_user.get("id") or ""),
            email=email,
            email_verified=verified,
            username_hint=login,
            first_name=first_name,
            last_name=last_name,
            raw=github_user,
        )
        return self._issue_tokens_for_profile(profile)

    def _issue_tokens_for_profile(self, profile: OAuthProfile) -> dict[str, Any]:
        if not profile.provider_user_id:
            raise OAuthProviderError("OAuth provider did not return a stable user id.")
        if not profile.email_verified:
            raise OAuthProviderError("OAuth provider email is not verified.")

        with transaction.atomic():
            social_account = (
                SocialAccount.objects.select_for_update()
                .filter(provider=profile.provider, provider_user_id=profile.provider_user_id)
                .select_related("user")
                .first()
            )

            if social_account:
                user = social_account.user
                self._assert_user_can_authenticate(user)
                self._sync_user_from_profile(user, profile)
                if social_account.email != profile.email or social_account.extra_data != self._safe_profile_data(profile):
                    social_account.email = profile.email
                    social_account.extra_data = self._safe_profile_data(profile)
                    social_account.save(update_fields=["email", "extra_data", "updated_at"])
            else:
                user = self._get_or_create_user(profile)
                try:
                    SocialAccount.objects.create(
                        user=user,
                        provider=profile.provider,
                        provider_user_id=profile.provider_user_id,
                        email=profile.email,
                        extra_data=self._safe_profile_data(profile),
                    )
                except IntegrityError:
                    social_account = SocialAccount.objects.select_related("user").get(
                        provider=profile.provider,
                        provider_user_id=profile.provider_user_id,
                    )
                    user = social_account.user

        self._assert_user_can_authenticate(user)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return {
            "token": str(access),
            "refreshToken": str(refresh),
            "expirationTime": int(access["exp"]) * 1000,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": getattr(user.role, "symbol", None),
                "emailVerified": user.email_verified,
            },
        }

    def _get_or_create_user(self, profile: OAuthProfile):
        user = User.objects.filter(email__iexact=profile.email).order_by("date_joined").first()
        if user:
            self._assert_user_can_authenticate(user)
            self._sync_user_from_profile(user, profile)
            return user

        user = User(
            username=self._build_unique_username(profile.username_hint),
            email=profile.email,
            first_name=profile.first_name[:150],
            last_name=profile.last_name[:150],
            role=self._default_role(),
            email_verified=True,
            phone_number=None,
        )
        user.set_unusable_password()
        user.save()
        return user

    def _sync_user_from_profile(self, user, profile: OAuthProfile) -> None:
        changed_fields: list[str] = []
        email_changed = False

        if profile.email and str(user.email or "").lower() != profile.email:
            conflict = User.objects.filter(email__iexact=profile.email).exclude(pk=user.pk).exists()
            if conflict:
                raise OAuthProviderError("This email is already linked to another account.")
            user.email = profile.email
            email_changed = True
            changed_fields.append("email")
        if profile.first_name and not user.first_name:
            user.first_name = profile.first_name[:150]
            changed_fields.append("first_name")
        if profile.last_name and not user.last_name:
            user.last_name = profile.last_name[:150]
            changed_fields.append("last_name")
        if not user.role_id:
            user.role = self._default_role()
            changed_fields.append("role")

        if changed_fields:
            user.save(update_fields=[*changed_fields, "updated_at"])

        # The model intentionally resets verification when an email changes. A
        # verified OAuth provider proves the new email, so mark it verified only
        # after the new address has been persisted.
        if profile.email_verified and (email_changed or not user.email_verified):
            user.email_verified = True
            user.save(update_fields=["email_verified", "updated_at"])

    def _default_role(self) -> Role:
        symbol = getattr(settings, "OAUTH_DEFAULT_USER_ROLE_SYMBOL", "user")
        role = Role.objects.filter(
            symbol=symbol,
            is_active=True,
            is_deleted=False,
        ).first()
        if not role:
            raise OAuthProviderError(
                "OAuth account provisioning is not configured.",
                status_code=500,
                log_message=f"Missing active OAuth default role: {symbol}",
            )
        return role

    @staticmethod
    def _assert_user_can_authenticate(user) -> None:
        if not user.is_active or getattr(user, "is_deleted", False):
            raise OAuthProviderError("This account is inactive.")

    def _build_unique_username(self, hint: str) -> str:
        base = re.sub(r"[^a-zA-Z0-9_.-]+", "", (hint or "user").strip().lower())[:120] or "user"
        username = base
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base}-{get_random_string(6).lower()}"[:150]
        return username

    def _resolve_github_email(self, *, github_user: dict[str, Any], headers: dict[str, str]) -> tuple[str, bool]:
        emails = self._get_json(self.GITHUB_EMAILS_URL, headers=headers)
        if not isinstance(emails, list):
            raise OAuthProviderError("GitHub email response was invalid.")

        primary = next(
            (item for item in emails if item.get("primary") and item.get("verified") and item.get("email")),
            None,
        )
        if primary:
            return primary["email"].lower().strip(), True

        raise OAuthProviderError(
            "GitHub account does not expose a verified primary email. Request the user:email scope."
        )

    @staticmethod
    def _safe_profile_data(profile: OAuthProfile) -> dict[str, Any]:
        raw = profile.raw or {}
        allowed_keys = {
            "sub", "id", "login", "name", "given_name", "family_name",
            "picture", "avatar_url", "html_url", "locale",
        }
        return {key: raw[key] for key in allowed_keys if key in raw}

    @staticmethod
    def _split_name(full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split(maxsplit=1)
        if not parts:
            return "", ""
        return parts[0], parts[1] if len(parts) > 1 else ""

    @staticmethod
    def _validate_redirect_uri(redirect_uri: str) -> None:
        allowed = getattr(settings, "OAUTH_ALLOWED_REDIRECT_URIS", [])
        if not allowed and not getattr(settings, "DEBUG", False):
            raise OAuthProviderError(
                "OAuth redirect URI allowlist is not configured.",
                status_code=500,
            )
        if allowed and redirect_uri not in allowed:
            raise OAuthProviderError("redirectUri is not allowed for OAuth login.")

    @staticmethod
    def _required_setting(name: str) -> str:
        value = getattr(settings, name, "")
        if not value:
            raise OAuthProviderError(
                "OAuth provider is not configured.",
                status_code=500,
                log_message=f"Missing required setting: {name}",
            )
        return value

    def _post_json(self, url: str, data: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            **(headers or {}),
        }
        request = Request(
            url,
            data=urlencode(data).encode("utf-8"),
            headers=request_headers,
            method="POST",
        )
        return self._open_json(request)

    def _get_json(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        request = Request(url, headers={"Accept": "application/json", **(headers or {})}, method="GET")
        return self._open_json(request)

    @staticmethod
    def _open_json(request: Request) -> dict[str, Any] | list[dict[str, Any]]:
        try:
            with urlopen(request, timeout=getattr(settings, "OAUTH_HTTP_TIMEOUT_SECONDS", 10)) as response:
                max_bytes = int(getattr(settings, "OAUTH_MAX_RESPONSE_BYTES", 1024 * 1024))
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > max_bytes:
                    raise OAuthProviderError("OAuth provider returned an oversized response.")
                raw_body = response.read(max_bytes + 1)
                if len(raw_body) > max_bytes:
                    raise OAuthProviderError("OAuth provider returned an oversized response.")
                body = raw_body.decode("utf-8")
        except HTTPError as exc:
            exc.read()
            logger.warning("OAuth provider HTTP error: status=%s", exc.code)
            raise OAuthProviderError("OAuth provider rejected the request.") from exc
        except URLError as exc:
            logger.warning("OAuth provider connection error: %s", exc)
            raise OAuthProviderError("OAuth provider is temporarily unavailable.") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            logger.warning("OAuth provider returned a non-JSON response.")
            raise OAuthProviderError("OAuth provider returned an invalid response.") from exc
