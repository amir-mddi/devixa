class StatusCodeConstant:
    HTTP_200_OK = {
        "en_msg": "Successfully",
        "code": 200,
        "status": "OK",
        "fa_msg": "با موفقیت انجام شد",
    }
    HTTP_201_CREATED = {
        "en_msg": "Successfully created",
        "fa_msg": "با موفقیت ایجاد شد",
        "code": 201,
        "status": "OK",
    }
    HTTP_202_ACCEPTED = {
        "en_msg": "Request accepted",
        "fa_msg": "درخواست پذیرفته شد",
        "code": 202,
        "status": "OK",
    }
    HTTP_204_NO_CONTENT = {
        "en_msg": "Successfully but with no content",
        "code": 204,
        "status": "OK",
        "fa_msg": "درخواست موفقیت آمیز بدون محتوا",
    }
    HTTP_205_RESET_CONTENT = {
        "en_msg": "Reset content",
        "code": 205,
        "status": "OK",
        "fa_msg": "بازنشانی محتوا",
    }
    HTTP_301_MOVED_PERMANENTLY = {
        "en_msg": "Moved permanently",
        "code": 301,
        "status": "REDIRECT",
        "fa_msg": "به صورت دائمی منتقل شده است",
    }
    HTTP_302_FOUND = {
        "en_msg": "Found",
        "code": 302,
        "status": "REDIRECT",
        "fa_msg": "یافت شد",
    }
    HTTP_303_SEE_OTHER = {
        "en_msg": "See other",
        "code": 303,
        "status": "REDIRECT",
        "fa_msg": "به مکان دیگری مراجعه کنید",
    }
    HTTP_304_NOT_MODIFIED = {
        "en_msg": "Not modified",
        "code": 304,
        "status": "OK",
        "fa_msg": "تغییری نکرده است",
    }
    HTTP_400_BAD_REQUEST = {
        "en_msg": "Bad Request",
        "code": 400,
        "status": "FAILED",
        "fa_msg": "درخواست معتبر نمی باشد",
    }
    HTTP_401_UNAUTHORIZED = {
        "en_msg": "Unauthorized",
        "code": 401,
        "status": "FAILED",
        "fa_msg": "اطلاعات مورد نیاز برای اعتبار سنجی ارسال نشده است",
    }
    HTTP_402_FORBIDDEN = {
        "en_msg": "Payment Required / Forbidden (custom)",
        "code": 402,
        "status": "FAILED",
        "fa_msg": "مجاز به پرداخت یا دسترسی نیستید",
    }
    HTTP_403_FORBIDDEN = {
        "en_msg": "Forbidden",
        "code": 403,
        "status": "FAILED",
        "fa_msg": "عدم دسترسی مجاز",
    }
    HTTP_404_NOT_FOUND = {
        "en_msg": "Not Found",
        "code": 404,
        "status": "FAILED",
        "fa_msg": "اطلاعات درخواستی یافت نشد",
    }
    HTTP_405_METHOD_NOT_ALLOWED = {
        "en_msg": "Method Not Allowed",
        "code": 405,
        "status": "FAILED",
        "fa_msg": "دسترسی به این اندپوینت مجاز نمی باشد",
    }
    HTTP_406_NOT_ACCEPTABLE = {
        "en_msg": "Not Acceptable",
        "code": 406,
        "status": "FAILED",
        "fa_msg": "درخواست قابل قبول نیست",
    }
    HTTP_407_REQUEST_TIMEOUT = {
        "en_msg": "Request Timeout",
        "code": 407,
        "status": "FAILED",
        "fa_msg": "مهلت درخواست به پایان رسیده است",
    }
    HTTP_408_GONE = {
        "en_msg": "Resource Gone",
        "code": 408,
        "status": "FAILED",
        "fa_msg": "ریسورس مورد نظر دیگر در دسترس نیست",
    }
    HTTP_409_CONFLICT = {
        "en_msg": "Conflict",
        "code": 409,
        "status": "FAILED",
        "fa_msg": "تعارض در داده‌ها",
    }
    HTTP_410_GONE = {
        "en_msg": "Gone",
        "code": 410,
        "status": "FAILED",
        "fa_msg": "ریسورس مورد نظر حذف شده است",
    }
    HTTP_411_NOT_IMPLEMENTED = {
        "en_msg": "Not Implemented",
        "code": 411,
        "status": "FAILED",
        "fa_msg": "پیاده‌سازی نشده است",
    }
    HTTP_412_PAYLOAD_TOO_LARGE = {
        "en_msg": "Payload Too Large",
        "code": 412,
        "status": "FAILED",
        "fa_msg": "اندازه درخواست بیش از حد مجاز است",
    }
    HTTP_415_UNSUPPORTED_MEDIA = {
        "en_msg": "Unsupported Media Type",
        "code": 415,
        "status": "FAILED",
        "fa_msg": "نوع رسانه پشتیبانی نمی‌شود",
    }
    HTTP_416_REQUESTED_RANGE_NOT_IMPLEMENTED = {
        "en_msg": "Requested Range Not Satisfiable",
        "code": 416,
        "status": "FAILED",
        "fa_msg": "محدوده درخواستی پشتیبانی نمی‌شود",
    }
    HTTP_417_EXPECTATION_FAILED = {
        "en_msg": "Expectation Failed",
        "code": 417,
        "status": "FAILED",
        "fa_msg": "انتظارات درخواست برآورده نشد",
    }
    HTTP_429_TOO_MANY_REQUESTS = {
        "en_msg": "Too Many Requests",
        "code": 429,
        "status": "FAILED",
        "fa_msg": "درخواست بیش از حد مجاز",
    }
    HTTP_500_INTERNAL_SERVER_ERROR = {
        "en_msg": "Internal Server Error",
        "code": 500,
        "status": "FAILED",
        "fa_msg": "خطای داخلی سرور",
    }
    HTTP_501_NOT_IMPLEMENTED = {
        "en_msg": "Not Implemented",
        "code": 501,
        "status": "FAILED",
        "fa_msg": "پیاده‌سازی نشده است",
    }
    HTTP_502_BAD_GATEWAY = {
        "en_msg": "Bad Gateway",
        "code": 502,
        "status": "FAILED",
        "fa_msg": "گیت‌وی نامعتبر است",
    }
    HTTP_503_SERVICE_UNAVAILABLE = {
        "en_msg": "Service Unavailable",
        "code": 503,
        "status": "FAILED",
        "fa_msg": "سرویس در دسترس نیست",
    }
    HTTP_504_GATEWAY_TIMEOUT = {
        "en_msg": "Gateway Timeout",
        "code": 504,
        "status": "FAILED",
        "fa_msg": "پاسخ از گیت‌وی دریافت نشد",
    }
    HTTP_510_TOO_MANY_REQUESTS = {
        "en_msg": "Too Many Requests",
        "code": 510,
        "status": "FAILED",
        "fa_msg": "تعداد درخواست‌ها بیش از حد مجاز است",
    }
    HTTP_511_REQUEST_TIMEOUT = {
        "en_msg": "Request Timeout",
        "code": 511,
        "status": "FAILED",
        "fa_msg": "مهلت درخواست تمام شده است",
    }
    HTTP_512_BAD_GATEWAY = {
        "en_msg": "Bad Gateway (Custom)",
        "code": 512,
        "status": "FAILED",
        "fa_msg": "گیت‌وی نامعتبر (سفارشی)",
    }
    HTTP_516_UNPROCESSABLE_ENTITY = {
        "en_msg": "Unprocessable Entity",
        "code": 516,
        "status": "FAILED",
        "fa_msg": "موجودیت غیرقابل پردازش است",
    }
    HTTP_517_LOADED = {
        "en_msg": "Resource Loaded",
        "code": 517,
        "status": "OK",
        "fa_msg": "ریسورس بارگذاری شد",
    }
