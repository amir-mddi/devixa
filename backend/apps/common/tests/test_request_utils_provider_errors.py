import httpx
from django.test import SimpleTestCase

from backend.apps.common.utils.request_utils import RequestUtils


class RequestUtilsProviderErrorTests(SimpleTestCase):
    def test_provider_error_extracts_status_without_message(self):
        response = httpx.Response(
            501,
            json={"return": {"status": 501, "message": "OTP secret 123456"}},
        )
        self.assertEqual(RequestUtils._safe_provider_error(response), "provider_status=501")

    def test_sms_phone_and_tokens_are_redacted_in_logs(self):
        result = RequestUtils._safe_log_params({
            "params": {"receptor": "09121234567", "token": "123456", "template": "VerifyPhoneNumber"}
        })
        self.assertEqual(result["params"]["receptor"], "***")
        self.assertEqual(result["params"]["token"], "***")
        self.assertEqual(result["params"]["template"], "VerifyPhoneNumber")
