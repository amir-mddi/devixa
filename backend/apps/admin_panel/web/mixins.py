from __future__ import annotations

import inspect

from asgiref.sync import sync_to_async
from django.contrib.auth.mixins import LoginRequiredMixin

from backend.apps.admin_panel.services import AdminPanelPermissionService


class AdminPanelAccessMixin(LoginRequiredMixin):
    permission_service_class = AdminPanelPermissionService
    login_url = "/login/"

    async def dispatch(self, request, *args, **kwargs):
        response = await sync_to_async(
            super().dispatch,
            thread_sensitive=True,
        )(request, *args, **kwargs)
        if inspect.isawaitable(response):
            return await response
        return response

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        self.permission_service_class.ensure_access(self.request.user)
        return super().handle_no_permission()

    def test_admin_access(self):
        self.permission_service_class.ensure_access(self.request.user)


class AdminPanelProtectedViewMixin(AdminPanelAccessMixin):
    async def dispatch(self, request, *args, **kwargs):
        is_authenticated = await sync_to_async(
            lambda: request.user.is_authenticated,
            thread_sensitive=True,
        )()
        if is_authenticated:
            await sync_to_async(
                self.test_admin_access,
                thread_sensitive=True,
            )()
        return await super().dispatch(request, *args, **kwargs)
