from __future__ import annotations

from django import template
from django.templatetags.static import static

from backend.apps.common.utils.common_utils import CommonUtils

register = template.Library()


@register.simple_tag
def project_static(path: str) -> str:
    return static(CommonUtils.build_project_static_path(path))
