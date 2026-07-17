from __future__ import annotations

from django.http import JsonResponse

from backend.apps.common.utils.async_middleware import AsyncCompatibleMiddleware
from backend.apps.common.web.ajax.value_objects import (
    AjaxRequestHeaderValueVO,
    AjaxRequestHeaderVO,
    AjaxResponseKeyVO,
)


class AjaxFormRedirectMiddleware(AsyncCompatibleMiddleware):
    """Expose same-origin form redirects to the jQuery navigation layer.

    Browsers follow XHR redirects internally and hide the original ``Location``
    value, including URL fragments.  Converting only AJAX form redirects to a
    small JSON contract lets the client fetch and swap the destination page
    while normal non-JavaScript form submissions keep Django's standard PRG
    behavior.
    """

    redirect_statuses = {301, 302, 303}
    unsafe_methods = {"POST", "PUT", "PATCH", "DELETE"}

    @staticmethod
    def _is_ajax_form_request(request) -> bool:
        requested_with = request.headers.get(
            AjaxRequestHeaderVO.REQUESTED_WITH.value,
            "",
        )
        ajax_form = request.headers.get(AjaxRequestHeaderVO.AJAX_FORM.value, "")
        return (
            request.method.upper() in AjaxFormRedirectMiddleware.unsafe_methods
            and requested_with == AjaxRequestHeaderValueVO.XML_HTTP_REQUEST.value
            and ajax_form.lower() == AjaxRequestHeaderValueVO.TRUE.value
        )

    @classmethod
    def _normalize(cls, request, response):
        if not cls._is_ajax_form_request(request):
            return response
        if response.status_code not in cls.redirect_statuses:
            return response

        redirect_url = response.headers.get("Location")
        if not redirect_url:
            return response

        return JsonResponse(
            {
                AjaxResponseKeyVO.SUCCESS.value: True,
                AjaxResponseKeyVO.REDIRECT_URL.value: redirect_url,
            }
        )

    def process_sync(self, request):
        return self._normalize(request, self.get_response(request))

    async def process_async(self, request):
        return self._normalize(request, await self.get_response(request))
