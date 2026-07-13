from __future__ import annotations

import secrets
import time
from hmac import compare_digest

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as django_login
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from dealio.apps.accounts.dtos.oauth_dto import OAuthAuthorizationRequestDTO
from dealio.apps.accounts.exceptions.oauth_exceptions import OAuthProviderError
from dealio.apps.accounts.enums.oauth_enums import OAuthProviderEnum, OAuthSessionKeyEnum
from dealio.apps.accounts.logic.oauth_logic import OAuthLoginLogic
from dealio.apps.accounts.services.oauth_service import SocialOAuthService
from dealio.apps.accounts.vo.oauth_vo import OAuthDefaultVO, OAuthMessageVO
from dealio.apps.accounts.web.value_objects import AccountWebReverseNameVO
from dealio.apps.common.helpers.decorators.rate_limit import rate_limit


class OAuthWebFlowMixin:
    provider: OAuthProviderEnum
    oauth_logic_class = OAuthLoginLogic
    oauth_service_class = SocialOAuthService

    def get_redirect_uri(self) -> str:
        setting_name = f"{self.provider.value.upper()}_OAUTH_WEB_REDIRECT_URI"
        configured = str(getattr(settings, setting_name, "") or "").strip()
        if configured:
            return configured
        return self.request.build_absolute_uri(
            reverse(f"accounts_web:oauth_{self.provider.value}_callback")
        )

    def safe_next_url(self, candidate: str | None) -> str:
        if candidate and url_has_allowed_host_and_scheme(
            candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return reverse(AccountWebReverseNameVO.PROFILE.value)


@method_decorator(rate_limit(authenticated_limit=10, anonymous_limit=10, period=300), name="dispatch")
class OAuthWebStartView(OAuthWebFlowMixin, View):
    def get(self, request, *args, **kwargs):
        state = secrets.token_urlsafe(32)
        redirect_uri = self.get_redirect_uri()
        next_url = self.safe_next_url(request.GET.get("next"))
        session_payload = {
            OAuthSessionKeyEnum.STATE.value: state,
            OAuthSessionKeyEnum.PROVIDER.value: self.provider.value,
            OAuthSessionKeyEnum.CREATED_AT.value: int(time.time()),
            OAuthSessionKeyEnum.NEXT_URL.value: next_url,
            OAuthSessionKeyEnum.REDIRECT_URI.value: redirect_uri,
        }
        request.session[OAuthSessionKeyEnum.FLOW.value] = session_payload
        request.session.modified = True

        try:
            authorization_url = self.oauth_logic_class().build_authorization_url(
                OAuthAuthorizationRequestDTO(
                    provider=self.provider.value,
                    redirect_uri=redirect_uri,
                    state=state,
                )
            )
        except OAuthProviderError as exc:
            messages.error(request, exc.public_message)
            return redirect(AccountWebReverseNameVO.LOGIN.value)
        return redirect(authorization_url)


@method_decorator(rate_limit(authenticated_limit=20, anonymous_limit=20, period=300), name="dispatch")
class OAuthWebCallbackView(OAuthWebFlowMixin, View):
    def get(self, request, *args, **kwargs):
        payload = request.session.get(OAuthSessionKeyEnum.FLOW.value)
        if not self._valid_state(payload, request.GET.get("state")):
            messages.error(request, OAuthMessageVO.INVALID_STATE.value)
            return redirect(AccountWebReverseNameVO.LOGIN.value)

        request.session.pop(OAuthSessionKeyEnum.FLOW.value, None)
        request.session.modified = True

        if request.GET.get("error"):
            messages.error(request, OAuthMessageVO.AUTHORIZATION_CANCELLED.value)
            return redirect(AccountWebReverseNameVO.LOGIN.value)

        code = str(request.GET.get("code") or "").strip()
        if not code:
            messages.error(request, OAuthMessageVO.PROVIDER_INVALID_RESPONSE.value)
            return redirect(AccountWebReverseNameVO.LOGIN.value)

        try:
            result = self.oauth_service_class().authenticate(
                provider=self.provider.value,
                code=code,
                redirect_uri=payload[OAuthSessionKeyEnum.REDIRECT_URI.value],
            )
        except OAuthProviderError as exc:
            messages.error(request, exc.public_message)
            return redirect(AccountWebReverseNameVO.LOGIN.value)

        django_login(request, result.user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, OAuthMessageVO.LOGIN_SUCCESS.value)
        return redirect(self.safe_next_url(payload.get(OAuthSessionKeyEnum.NEXT_URL.value)))

    def _valid_state(self, payload, returned_state: str | None) -> bool:
        if not isinstance(payload, dict):
            return False
        expected_state = str(payload.get(OAuthSessionKeyEnum.STATE.value) or "")
        provider = str(payload.get(OAuthSessionKeyEnum.PROVIDER.value) or "")
        try:
            created_at = int(payload.get(OAuthSessionKeyEnum.CREATED_AT.value) or 0)
        except (TypeError, ValueError):
            return False
        ttl = max(
            60,
            int(getattr(settings, "OAUTH_STATE_TTL_SECONDS", OAuthDefaultVO.STATE_TTL_SECONDS.value)),
        )
        return (
            bool(expected_state)
            and bool(returned_state)
            and compare_digest(expected_state, str(returned_state))
            and provider == self.provider.value
            and 0 <= int(time.time()) - created_at <= ttl
        )


class GoogleOAuthWebStartView(OAuthWebStartView):
    provider = OAuthProviderEnum.GOOGLE


class GoogleOAuthWebCallbackView(OAuthWebCallbackView):
    provider = OAuthProviderEnum.GOOGLE


class GitHubOAuthWebStartView(OAuthWebStartView):
    provider = OAuthProviderEnum.GITHUB


class GitHubOAuthWebCallbackView(OAuthWebCallbackView):
    provider = OAuthProviderEnum.GITHUB
