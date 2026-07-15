from __future__ import annotations

from enum import IntEnum, StrEnum


class RecaptchaEndpointVO(StrEnum):
    SITE_VERIFY = "https://www.google.com/recaptcha/api/siteverify"
    CLIENT_SCRIPT = "https://www.google.com/recaptcha/api.js"


class RecaptchaRequestFieldVO(StrEnum):
    SECRET = "secret"
    RESPONSE = "response"
    REMOTE_IP = "remoteip"


class RecaptchaResponseFieldVO(StrEnum):
    SUCCESS = "success"
    SCORE = "score"
    ACTION = "action"
    HOSTNAME = "hostname"
    CHALLENGE_TIMESTAMP = "challenge_ts"
    ERROR_CODES = "error-codes"


class RecaptchaSettingNameVO(StrEnum):
    ENABLED = "RECAPTCHA_ENABLED"
    SITE_KEY = "RECAPTCHA_SITE_KEY"
    SECRET_KEY = "RECAPTCHA_SECRET_KEY"
    MIN_SCORE = "RECAPTCHA_MIN_SCORE"
    ALLOWED_HOSTNAMES = "RECAPTCHA_ALLOWED_HOSTNAMES"
    HTTP_TIMEOUT_SECONDS = "RECAPTCHA_HTTP_TIMEOUT_SECONDS"
    MAX_RESPONSE_BYTES = "RECAPTCHA_MAX_RESPONSE_BYTES"
    SEND_REMOTE_IP = "RECAPTCHA_SEND_REMOTE_IP"


class RecaptchaDefaultVO(IntEnum):
    HTTP_TIMEOUT_SECONDS = 5
    MAX_RESPONSE_BYTES = 65536


class RecaptchaLogMessageVO(StrEnum):
    PROVIDER_HTTP_ERROR = "reCAPTCHA verification HTTP error: status={status}"
    PROVIDER_CONNECTION_ERROR = "reCAPTCHA verification connection error: {error}"
    PROVIDER_INVALID_RESPONSE = "reCAPTCHA returned an invalid response."
    PROVIDER_REJECTED = "reCAPTCHA rejected the token: errors={error_codes}"
    ACTION_MISMATCH = "reCAPTCHA action mismatch: expected={expected}, actual={actual}"
    SCORE_TOO_LOW = "reCAPTCHA score below threshold: score={score}, threshold={threshold}"
    HOSTNAME_MISMATCH = "reCAPTCHA hostname mismatch: hostname={hostname}"
