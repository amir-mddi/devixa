import ast

from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response

from dealio.apps.common.response_serializer import ResponseSerializer
from dealio.apps.core_models.constants.common_vo import ResponseVO, ResponseTypeVO
from dealio.apps.core_models.constants.status_codes import StatusCodeConstant
from dealio.apps.core_models.dtos.data_dto import DataDto


class ResponseUtil(Response):
    def __init__(self, data=None, status_code: str = ResponseVO.http_200,
                 custom_fields: dict = None):
        extra_data = getattr(StatusCodeConstant, str(status_code))
        data = DataDto(data=data).model_dump()
        data.update(extra_data)
        if custom_fields:
            data.update(custom_fields)
        super().__init__(data=data, status=extra_data.get("code"))
        self["Content-Type"] = "application/json; charset=utf-8"


class JsonResponseUtil(JsonResponse):
    def __init__(self, data=None, status_code: str = ResponseVO.http_200,
                 custom_fields: dict = None):
        if isinstance(data, str) and data is not None:
            try:
                data = ast.literal_eval(data)
            except (SyntaxError, ValueError):
                data = None
        extra_data = getattr(StatusCodeConstant, str(status_code))
        data = DataDto(data=data).model_dump()
        data.update(extra_data)
        if custom_fields:
            data = {}
            data.update(custom_fields)

        super().__init__(
            data=data,
            status=extra_data.get("code"),
            json_dumps_params={"ensure_ascii": False},
            content_type="application/json; charset=utf-8",
        )


class CommonJsonResponse(JsonResponse):
    def __init__(
            self,
            data: list | dict | None = None,
            status_code: int = status.HTTP_200_OK,
            code: str = ResponseTypeVO.ok,
            message: str = ResponseTypeVO.ok,
            status: str = ResponseTypeVO.ok,
    ):
        response = ResponseSerializer(
            {
                ResponseTypeVO.status_code: status_code,
                ResponseTypeVO.code: code,
                ResponseTypeVO.data: data,
                ResponseTypeVO.status: status,
                ResponseTypeVO.message: message,
            }
        )

        super().__init__(
            data=response.data,
            status=status_code,
            json_dumps_params={"ensure_ascii": False},
            content_type="application/json; charset=utf-8",
        )
