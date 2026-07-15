from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from backend.apps.accounts.dtos.recaptcha_dto import RecaptchaVerificationDTO
from backend.apps.accounts.entities.recaptcha_entity import RecaptchaProviderResponseEntity
from backend.apps.accounts.enums.recaptcha_enums import (
    RecaptchaActionEnum,
    RecaptchaFailureReasonEnum,
)
from backend.apps.accounts.exceptions.recaptcha_exceptions import RecaptchaProviderError
from backend.apps.accounts.logic.recaptcha_logic import RecaptchaVerificationLogic


class FakeRecaptchaRepository:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.last_dto = None

    def verify(self, dto):
        self.last_dto = dto
        if self.error:
            raise self.error
        return self.response


@override_settings(
    RECAPTCHA_ENABLED=True,
    RECAPTCHA_MIN_SCORE=0.5,
    RECAPTCHA_ALLOWED_HOSTNAMES=["acdevixa.ir", "www.acdevixa.ir"],
)
class RecaptchaVerificationLogicTests(SimpleTestCase):
    def _dto(self, token="token"):
        return RecaptchaVerificationDTO(
            token=token,
            expected_action=RecaptchaActionEnum.LOGIN,
            remote_ip="203.0.113.10",
        )

    def _response(self, **overrides):
        data = {
            "success": True,
            "score": 0.9,
            "action": RecaptchaActionEnum.LOGIN.value,
            "hostname": "acdevixa.ir",
            "challenge_timestamp": "2026-07-14T12:00:00Z",
            "error_codes": (),
        }
        data.update(overrides)
        return RecaptchaProviderResponseEntity(**data)

    def test_accepts_valid_provider_response(self):
        repository = FakeRecaptchaRepository(self._response())

        result = RecaptchaVerificationLogic(repository=repository).verify(self._dto())

        self.assertTrue(result.is_allowed)
        self.assertEqual(result.reason, RecaptchaFailureReasonEnum.VERIFIED)
        self.assertEqual(repository.last_dto.remote_ip, "203.0.113.10")

    def test_rejects_missing_token(self):
        result = RecaptchaVerificationLogic(
            repository=FakeRecaptchaRepository(self._response())
        ).verify(self._dto(token=""))

        self.assertFalse(result.is_allowed)
        self.assertEqual(result.reason, RecaptchaFailureReasonEnum.MISSING_TOKEN)

    def test_rejects_action_mismatch(self):
        result = RecaptchaVerificationLogic(
            repository=FakeRecaptchaRepository(
                self._response(action=RecaptchaActionEnum.REGISTER.value)
            )
        ).verify(self._dto())

        self.assertFalse(result.is_allowed)
        self.assertEqual(result.reason, RecaptchaFailureReasonEnum.ACTION_MISMATCH)

    def test_rejects_low_score(self):
        result = RecaptchaVerificationLogic(
            repository=FakeRecaptchaRepository(self._response(score=0.2))
        ).verify(self._dto())

        self.assertFalse(result.is_allowed)
        self.assertEqual(result.reason, RecaptchaFailureReasonEnum.SCORE_TOO_LOW)

    def test_rejects_unexpected_hostname(self):
        result = RecaptchaVerificationLogic(
            repository=FakeRecaptchaRepository(
                self._response(hostname="attacker.example")
            )
        ).verify(self._dto())

        self.assertFalse(result.is_allowed)
        self.assertEqual(result.reason, RecaptchaFailureReasonEnum.HOSTNAME_MISMATCH)

    def test_fails_closed_when_provider_is_unavailable(self):
        result = RecaptchaVerificationLogic(
            repository=FakeRecaptchaRepository(
                error=RecaptchaProviderError("provider unavailable")
            )
        ).verify(self._dto())

        self.assertFalse(result.is_allowed)
        self.assertEqual(
            result.reason,
            RecaptchaFailureReasonEnum.PROVIDER_UNAVAILABLE,
        )

    @override_settings(RECAPTCHA_ENABLED=False)
    def test_disabled_recaptcha_does_not_call_provider(self):
        repository = FakeRecaptchaRepository(error=AssertionError("must not be called"))

        result = RecaptchaVerificationLogic(repository=repository).verify(self._dto(token=""))

        self.assertTrue(result.is_allowed)
        self.assertEqual(result.reason, RecaptchaFailureReasonEnum.DISABLED)
