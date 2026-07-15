from concurrent.futures import Future
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from backend.apps.core_models.dtos.sms_providers.kavenegar_params_dto import (
    KavenegarTemplateSmsDTO,
)
from backend.apps.core_models.enum.general_enum import RequestMethod
from backend.apps.shared.repositories.adapters.kavenegar_adapter import KavenegarSmsService
from backend.apps.shared.repositories.logic import SharedApplicationLogic
from backend.tests.mixins import IsolatedServiceTestMixin


class KavenegarSmsServiceTests(SimpleTestCase):
    @patch("backend.apps.shared.repositories.adapters.kavenegar_adapter.RequestUtils.request")
    def test_send_sms_maps_only_defined_template_tokens(self, request_mock):
        response = MagicMock()
        response.json.return_value = {"return": {"status": 200}}
        request_mock.return_value = response
        service = KavenegarSmsService()
        service.api_key = "test-api-key"

        result = service.send_sms(
            KavenegarTemplateSmsDTO(
                recipient_phone_number="09121234567",
                template_name="VerifyPhoneNumber",
                token="123456",
                token2="5",
            )
        )

        self.assertEqual(result, {"return": {"status": 200}})
        request_mock.assert_called_once_with(
            url="https://api.kavenegar.com/v1/test-api-key/verify/lookup.json",
            method=RequestMethod.GET,
            params={
                "receptor": "09121234567",
                "template": "VerifyPhoneNumber",
                "token": "123456",
                "token2": "5",
            },
            rotate_proxy_on_error=False,
            redact_url=True,
        )

    def test_send_in_thread_submits_synchronous_adapter_method(self):
        service = KavenegarSmsService()
        dto = KavenegarTemplateSmsDTO(
            recipient_phone_number="09121234567",
            template_name="VerifyPhoneNumber",
            token="123456",
        )
        completed_future = Future()
        completed_future.set_result({"ok": True})
        executor = MagicMock()
        executor.submit.return_value = completed_future
        service._executor = executor

        returned_future = service.send_in_thread(dto)

        self.assertIs(returned_future, completed_future)
        executor.submit.assert_called_once_with(service.send_sms, dto)


class SharedSmsLogicTests(IsolatedServiceTestMixin, SimpleTestCase):
    def test_send_sms_delegates_to_async_provider(self):
        logic = SharedApplicationLogic()
        logic.sms_provider = MagicMock()
        future = Future()
        future.set_result({"ok": True})
        logic.sms_provider.send_in_thread.return_value = future
        dto = KavenegarTemplateSmsDTO(
            recipient_phone_number="09121234567",
            template_name="ForgotPassword",
            token="123456",
        )

        result = logic.send_sms(dto)

        self.assertIs(result, future)
        logic.sms_provider.send_in_thread.assert_called_once_with(dto)
