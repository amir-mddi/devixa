from django.contrib.auth import get_user_model

from dealio.apps.common.utils.request_utils import RequestUtils
from dealio.apps.core_models.constants.recaptcha_goole import RecaptchaConfig
from dealio.apps.core_models.enum.general_enum import RequestMethod


class ValidateReCaptcha:

    def check_user_exist(self, username: str, password: str):
        User = get_user_model()
        service_user = User.objects.get(username=username)
        if service_user and service_user.check_password(password):
            return service_user
        return

    def validate(self, request):
        service_user = self.check_user_exist(username=request.data.get("username"), password=request.data.get(
            "password"))
        if service_user and service_user.is_service_user:
            return True

        recaptcha_response = request.data.get('recaptcha', '')
        data = {
            'secret': RecaptchaConfig.secret_key,
            'response': recaptcha_response
        }
        response = RequestUtils.request_with_retry(url=RecaptchaConfig.request_url, data=data,
                                                   method=RequestMethod.POST)
        result = response.json()
        if result.get('success') and result.get("score") >= RecaptchaConfig.risk_score:
            return True
        return False
