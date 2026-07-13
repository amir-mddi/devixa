from django.contrib import admin

from dealio.apps.shared.models import ApiKeyManagerModel, ProjectConfigModel


@admin.register(ApiKeyManagerModel)
class ApiKeyManagerModelAdmin(admin.ModelAdmin):
    list_display = ("masked_api_key", "status", "is_active", "created_at")
    search_fields = ("api_key",)
    list_filter = ("status", "is_active")
    readonly_fields = ("masked_api_key",)

    def get_fields(self, request, obj=None):
        # Accept the secret only when creating a key. The change form never
        # renders the stored plaintext value back into HTML.
        if obj is None:
            return ("api_key", "status", "is_active")
        return ("masked_api_key", "status", "is_active")

    @admin.display(description="API key")
    def masked_api_key(self, obj):
        value = str(obj.api_key or "")
        if len(value) <= 8:
            return "********" if value else ""
        return f"{value[:4]}…{value[-4:]}"


@admin.register(ProjectConfigModel)
class ProjectConfigModelAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "slug",
        "contact_email",
        "support_email",
        "is_active",
    )
    search_fields = ("name", "display_name", "slug", "contact_email", "support_email")
    fieldsets = (
        (
            "Identity",
            {
                "fields": (
                    "singleton_key",
                    "name",
                    "display_name",
                    "slug",
                    "description",
                    "tagline",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "email_domain",
                    "contact_email",
                    "support_email",
                    "sales_email",
                    "partnership_email",
                    "phone",
                    "address",
                    "working_hours",
                )
            },
        ),
        (
            "Social",
            {
                "fields": (
                    "github_url",
                    "linkedin_url",
                    "telegram_url",
                    "instagram_url",
                    "telegram_bot_url",
                    "bale_bot_url",
                    "rubika_bot_url",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                    "is_deleted",
                    "deleted_at",
                )
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")
