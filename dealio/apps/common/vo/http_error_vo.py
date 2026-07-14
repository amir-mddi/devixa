class HttpErrorCodeVO:
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    RATE_LIMIT_CLIENT_UNKNOWN = "rate_limit_client_unknown"

    CSRF_ORIGIN_REJECTED = "csrf_origin_rejected"
    CSRF_REFERER_REJECTED = "csrf_referer_rejected"
    CSRF_COOKIE_MISSING = "csrf_cookie_missing"
    CSRF_TOKEN_MISSING = "csrf_token_missing"
    CSRF_TOKEN_INVALID = "csrf_token_invalid"
    CSRF_VALIDATION_FAILED = "csrf_validation_failed"


class HttpErrorTextVO:
    RATE_LIMIT_TITLE = "درخواست‌های بیش از حد"
    RATE_LIMIT_MESSAGE = (
        "تعداد درخواست‌های شما بیش از حد مجاز است. "
        "لطفاً {waiting_time} ثانیه دیگر دوباره تلاش کنید."
    )
    RATE_LIMIT_CLIENT_UNKNOWN_TITLE = "شناسایی درخواست ناموفق بود"
    RATE_LIMIT_CLIENT_UNKNOWN_MESSAGE = (
        "امکان شناسایی امن درخواست شما وجود ندارد. "
        "صفحه را تازه‌سازی کنید و دوباره تلاش کنید."
    )

    CSRF_TITLE = "درخواست امنیتی نامعتبر"
    CSRF_ORIGIN_MESSAGE = (
        "این درخواست از مبدأیی ارسال شده که سرور آن را معتبر نمی‌شناسد. "
        "صفحه را فقط از نشانی اصلی سایت باز کنید و دوباره تلاش کنید."
    )
    CSRF_REFERER_MESSAGE = (
        "نشانی صفحه ارسال‌کننده درخواست معتبر نیست. "
        "صفحه را از نشانی اصلی سایت دوباره باز کنید."
    )
    CSRF_COOKIE_MISSING_MESSAGE = (
        "کوکی امنیتی فرم پیدا نشد. کوکی‌های سایت را فعال کنید، "
        "صفحه را تازه‌سازی کنید و فرم را دوباره بفرستید."
    )
    CSRF_TOKEN_MISSING_MESSAGE = (
        "توکن امنیتی فرم ارسال نشده است. صفحه را تازه‌سازی کنید "
        "و فرم را دوباره بفرستید."
    )
    CSRF_TOKEN_INVALID_MESSAGE = (
        "توکن امنیتی فرم نامعتبر یا منقضی شده است. "
        "صفحه را تازه‌سازی کنید و دوباره تلاش کنید."
    )
    CSRF_GENERIC_MESSAGE = (
        "اعتبارسنجی امنیتی درخواست ناموفق بود. صفحه را تازه‌سازی کنید "
        "و عملیات را دوباره انجام دهید."
    )

    ERROR_PAGE_RETRY = "تلاش دوباره"
    ERROR_PAGE_HOME = "بازگشت به خانه"
    ERROR_PAGE_LOGIN = "بازگشت به ورود"
    ERROR_PAGE_STATUS_LABEL = "کد پاسخ"
    ERROR_PAGE_WAIT_LABEL = "زمان باقی‌مانده"
    ERROR_PAGE_SECONDS = "ثانیه"
