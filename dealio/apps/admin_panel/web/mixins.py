from django.contrib.auth.mixins import LoginRequiredMixin

from dealio.apps.admin_panel.services import AdminPanelPermissionService


class AdminPanelAccessMixin(LoginRequiredMixin):
    permission_service_class = AdminPanelPermissionService
    login_url = "/login/"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        self.permission_service_class.ensure_access(self.request.user)
        return super().handle_no_permission()

    def test_admin_access(self):
        self.permission_service_class.ensure_access(self.request.user)


class AdminPanelProtectedViewMixin(AdminPanelAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.test_admin_access()
        return super().dispatch(request, *args, **kwargs)
