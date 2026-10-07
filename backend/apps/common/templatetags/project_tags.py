from __future__ import annotations

from django import template
from django.templatetags.static import static

from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.common.utils.network_security import force_https_scheme

register = template.Library()


@register.simple_tag
def project_static(path: str) -> str:
    return static(CommonUtils.build_project_static_path(path))


@register.filter(name="https_url")
def https_url(value: object) -> str:
    """Upgrade a public HTTP URL to HTTPS at the final rendering boundary."""

    return force_https_scheme(str(value or ""))
