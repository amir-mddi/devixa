
from django.urls import resolve
from django.urls.exceptions import Resolver404

from dealio.apps.common.response_utils import JsonResponseUtil
from dealio.apps.common.utils.common_utils import CommonUtils
from dealio.apps.core_models.constants.common_vo import ResponseVO, ExcludeViewResponseVO
from dealio.project.settings import DEBUG

logger = CommonUtils.get_project_logger(__name__)


class GeneralResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        try:
            if not DEBUG:
                resolve(path)
        except Resolver404:
            return JsonResponseUtil(status_code=ResponseVO.http_404)

        if not path.endswith("/"):
            request.path += "/"
        # if not any(url in request.path for url in ExcludeViewResponseVO.urls if url != '/'):
        if request.path.startswith(f"{ExcludeViewResponseVO.api_urls_include}"):
            response = self.get_response(request)
            status_code = getattr(
                ResponseVO, ResponseVO.started_by + str(response.status_code)
            )
            if not status_code.startswith(ResponseVO.exception_identifier):
                if getattr(response, "data", False):
                    if not isinstance(response.data, dict):
                        response.data = CommonUtils.convert_py_object_to_dict(response.data)
                    if (
                            not isinstance(response.data, list)
                            and response
                            and response.data.get("fa_msg")
                    ):
                        return response
                    context = response.data
                else:
                    context = response.content.decode("utf-8")
                return JsonResponseUtil(data=context, status_code=status_code)
        return self.get_response(request)
