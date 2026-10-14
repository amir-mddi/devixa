from django.contrib import admin
from backend.apps.software_services.models import SoftwareProjectRequest


@admin.register(SoftwareProjectRequest)
class SoftwareProjectRequestAdmin(admin.ModelAdmin):
    list_display = ("project_title", "full_name", "category", "status", "budget", "created_at")
    list_filter = ("status", "category", "budget", "created_at")
    search_fields = ("project_title", "full_name", "email", "phone", "description")
    readonly_fields = ("id", "customer", "full_name", "email", "phone", "category", "project_title", "description", "budget", "timeline", "reference_url", "created_at", "updated_at")
    fields = ("id", "created_at", "updated_at", "status", "staff_note", "customer", "full_name", "email", "phone", "category", "project_title", "description", "budget", "timeline", "reference_url")
    list_per_page = 40
    def has_add_permission(self, request):
        return False
