import os


class ResponseVO:
    started_by = "http_"
    http_200 = "HTTP_200_OK"
    http_201 = "HTTP_201_CREATED"
    http_202 = "HTTP_202_ACCEPTED"
    http_203 = "HTTP_203_REDIRECT"
    http_204 = "HTTP_204_NO_CONTENT"
    http_205 = "HTTP_205_REDIRECT"
    http_301 = "HTTP_301_MOVED_PERMANENTLY"
    http_302 = "HTTP_302_FOUND"
    http_303 = "HTTP_303_SEE_OTHER"
    http_304 = "HTTP_304_NOT_MODIFIED"
    http_400 = "HTTP_400_BAD_REQUEST"
    http_401 = "HTTP_401_UNAUTHORIZED"
    http_402 = "HTTP_402_FORBIDDEN"
    http_403 = "HTTP_403_FORBIDDEN"
    http_404 = "HTTP_404_NOT_FOUND"
    http_405 = "HTTP_405_METHOD_NOT_ALLOWED"
    http_406 = "HTTP_406_NOT_ACCEPTABLE"
    http_407 = "HTTP_407_PROXY_AUTHENTICATION_REQUIRED"
    http_408 = "HTTP_408_REQUIRED"
    http_409 = "HTTP_409_CONFLICT"
    http_410 = "HTTP_410_GONE"
    http_411 = "HTTP_411_BAD_GATEWAY"
    http_412 = "HTTP_412_PRECONDITION"
    http_413 = "HTTP_413_PRECONDITION_REQUIRED"
    http_414 = "HTTP_414_REQUIRED"
    http_415 = "HTTP_415_UNSUPPORTED"
    http_416 = "HTTP_416_TOO_MANY_REQUESTS"
    http_417 = "HTTP_417_EXPECTATION_FAILED"
    http_429 = "HTTP_429_TOO_MANY_REQUESTS"
    http_500 = "HTTP_500_INTERNAL_SERVER_ERROR"
    http_501 = "HTTP_501_NOT_IMPLEMENTED"
    http_502 = "HTTP_502_BAD_GATEWAY"
    http_503 = "HTTP_503_SERVICE_UNAVAILABLE"
    http_504 = "HTTP_504_GATEWAY_TIMEOUT"
    http_505 = "HTTP_505_PROXY_AUTHENTICATION_REQUIRED"
    http_506 = "HTTP_506_TOO_MANY_REQUESTS"
    http_507 = "HTTP_507_PROXY_AUTHENTICATION_REQUIRED"
    http_508 = "HTTP_508_GONE"
    http_510 = "HTTP_510_BAD_GATEWAY"
    http_511 = "HTTP_511_UNSUPPORTED"
    http_512 = "HTTP_512_BAD_GATEWAY"
    http_513 = "HTTP_513_TOO_MANY_REQUESTS"
    http_514 = "HTTP_514_TOO_LARGE"
    http_515 = "HTTP_515_TOO_MANY_BYTES"
    http_516 = "HTTP_516_TOO_LARGE"
    http_517 = "HTTP_517_ABORTED"
    exception_identifier = "HTTP_5"


class ExcludeViewResponseVO:
    urls = [
        "schema",
        "schema/redoc",
        "schema/swagger-ui",
        "/",
        f"{os.environ.get('ADMIN_PANEL_URL', 'admin')}",
    ]
    api_urls_include = "/api"
    especial_field = "fa_msg"




class HttpConfigVO:
    http = "http://"
    https = "https://"



class ResponseTypeVO:
    # keys
    status = 'status'
    code = 'code'
    data = 'data'
    message = 'message'
    status_code = 'status_code'
    ok = 'OK'
    failed = 'FAILED'
    # codes
    success_code = 'success'
    update_code = 'updating'
    delete_code = 'deleting'
    create_code = 'creating'
    invalid_input_code = 'invalid_input'
    invalid_token_code = 'invalid_token'
    invalid_url_code = 'invalid_url'
    invalid_internal_error_code = 'internal_error'
    # messages
    success_msg = 'Successfully Retrieve Data'
    created_msg = 'Successfully Object Created'
    updated_msg = 'Successfully Object Updated'
    deleted_msg = 'Successfully Object Deleted'
    invalid_input_msg = 'Invalid Input Data'
    invalid_token_msg = 'Invalid Token Provided'
    invalid_url_msg = 'Invalid URL Provided'
    invalid_internal_error_msg = 'Internal Error Occurred'