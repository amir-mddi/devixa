from __future__ import annotations

from asgiref.sync import sync_to_async
from backend.apps.common.web.async_view import AsyncWebViewMixin

import os

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View

from backend.apps.common.project_config import get_request_project_context
from backend.apps.common.web.seo.adapters.request_url_adapter import SeoRequestUrlAdapter
from backend.apps.common.web.seo.logic.sitemap_logic import SeoSitemapLogic
from backend.apps.common.web.seo.value_objects.seo_vo import (
    SeoRobotsDisallowPathVO,
    SeoRouteVO,
    SeoTemplateVO,
)


class SeoSitemapView(AsyncWebViewMixin, View):
    sitemap_logic_class = SeoSitemapLogic

    async def get(self, request, *args, **kwargs):
        return await sync_to_async(self._sync_get, thread_sensitive=True)(request, *args, **kwargs)

    def _sync_get(self, request, *args, **kwargs):
        content = render_to_string(SeoTemplateVO.SITEMAP.value, {'urls': self.sitemap_logic_class().build(request, get_request_project_context(request))})
        response = HttpResponse(content, content_type='application/xml; charset=utf-8')
        response['Cache-Control'] = 'public, max-age=3600'
        return response


class RobotsTxtView(AsyncWebViewMixin, View):
    async def get(self, request, *args, **kwargs):
        return await sync_to_async(self._sync_get, thread_sensitive=True)(request, *args, **kwargs)

    def _sync_get(self, request, *args, **kwargs):
        project = get_request_project_context(request)
        sitemap_url = SeoRequestUrlAdapter.from_project(request, project).absolute_url(reverse(SeoRouteVO.SITEMAP.value))
        admin_path = '/' + os.environ.get('ADMIN_PANEL_URL', 'admin/').strip('/') + '/'
        disallowed_paths = tuple(dict.fromkeys((admin_path, *(path.value for path in SeoRobotsDisallowPathVO))))
        lines = ['User-agent: *', 'Allow: /']
        lines.extend((f'Disallow: {path}' for path in disallowed_paths))
        lines.extend(('', f'Sitemap: {sitemap_url}'))
        response = HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')
        response['Cache-Control'] = 'public, max-age=3600'
        return response
