from dealio.apps.common.response_utils import JsonResponseUtil
from dealio.apps.common.utils.common_utils import CommonUtils
from dealio.apps.core_models.constants.common_vo import ExcludeViewResponseVO, ResponseVO


class GeneralResponseMiddleware:
    """Apply the project response envelope without rewriting request paths."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.startswith(ExcludeViewResponseVO.api_urls_include):
            return response

        status_code = getattr(
            ResponseVO,
            ResponseVO.started_by + str(response.status_code),
            ResponseVO.http_500,
        )
        if str(status_code).startswith(ResponseVO.exception_identifier):
            return response

        if getattr(response, "data", None) is not None:
            if not isinstance(response.data, (dict, list)):
                response.data = CommonUtils.convert_py_object_to_dict(response.data)
            if isinstance(response.data, dict) and response.data.get("fa_msg"):
                return response
            context = response.data
        else:
            try:
                context = response.content.decode("utf-8")
            except (AttributeError, UnicodeDecodeError):
                return response

        return JsonResponseUtil(data=context, status_code=status_code)
