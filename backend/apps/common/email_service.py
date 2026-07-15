# apps/common/email_service.py

from backend.apps.common.utils.common_utils import CommonUtils
from threading import Thread

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from backend.apps.common.project_config import get_project_name

logger = CommonUtils.get_project_logger(__name__)


def send_html_email(
    *,
    subject: str,
    template_name: str,
    context: dict,
    recipient_list: list[str],
    from_email: str | None = None,
) -> None:
    safe_context = {
        "app_name": get_project_name(),
        "current_year": timezone.now().year,
        **(context or {}),
    }
    html_content = render_to_string(template_name, safe_context)
    text_content = strip_tags(html_content)

    sender_email = from_email or settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER

    if not sender_email:
        raise ValueError(
            "Email sender is not configured. Set EMAIL_HOST_USER or DEFAULT_FROM_EMAIL."
        )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=sender_email,
        to=recipient_list,
    )

    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


def send_html_email_async(
    *,
    subject: str,
    template_name: str,
    context: dict,
    recipient_list: list[str],
    from_email: str | None = None,
) -> Thread:
    def _send_email():
        try:
            send_html_email(
                subject=subject,
                template_name=template_name,
                context=context,
                recipient_list=recipient_list,
                from_email=from_email,
            )
        except Exception:
            logger.exception("Failed to send email asynchronously.")

    thread = Thread(target=_send_email, daemon=True)
    thread.start()

    return thread
