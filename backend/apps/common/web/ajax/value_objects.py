from enum import StrEnum


class AjaxRequestHeaderVO(StrEnum):
    REQUESTED_WITH = "X-Requested-With"
    AJAX_FORM = "X-Ajax-Form"


class AjaxRequestHeaderValueVO(StrEnum):
    XML_HTTP_REQUEST = "XMLHttpRequest"
    TRUE = "true"


class AjaxResponseKeyVO(StrEnum):
    SUCCESS = "success"
    REDIRECT_URL = "redirect_url"
