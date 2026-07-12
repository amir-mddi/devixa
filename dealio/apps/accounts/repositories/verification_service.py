from dealio.apps.accounts.repositories.adapters.email_adapter import AccountEmailAdapter


def send_email_verification_code(user) -> None:
    AccountEmailAdapter().send_email_verification_code(user)
