class CommonVO:
    http = "http://"
    https = "https://"
    dirs_skip_creation_init = [".git", "venv", ".idea"]
    true_boolean_input_query_parameter = ("1", "true", "yes", "y", "t")


class KavenegarVo:
    password_recovery = "passwordRecovery"
    create_account = "createAccount"
    alert = "alert"
    change_password = "ChangePassword"
    validation_identifier = "ValidationIdentifier"
    verification_code = "VerificationCode"


class ResponseVO:
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


class UserRoleVO:
    ADMIN = 'admin'
    USER = 'user'


class ReqHeaderVO:
    accept = '*/*'
    content_type = 'application/json'
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"

    @classmethod
    def header(cls):
        return {'Content-Type': cls.content_type, 'accept': cls.accept, 'User-Agent': cls.user_agent}


class EnvVO:
    local = "local"
    development = "development"
    testing = "testing"
    production = "production"


class CeleryTasksVO:
    tasks = [
        'intervention.tasks.aggressive_sc',
        'intervention.tasks.others',
        'intervention.tasks.reduce_sc',
        'intervention.tasks.rsi_sc',
        'intervention.tasks.shared_tasks',
        'intervention.tasks.buy_sc',
    ]
    timezone = 'Asia/Tehran'
