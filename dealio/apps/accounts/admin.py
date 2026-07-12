from django.contrib import admin

from dealio.apps.accounts.models import CustomUser, Access, Role, SocialAccount


class UserAgentAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'role')


class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_accesses',)

    def display_accesses(self, obj):
        return ', '.join([str(access) for access in obj.accesses.all()])

    display_accesses.short_description = 'Accesses'


class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("provider", "email", "user", "created_at")
    list_filter = ("provider",)
    search_fields = ("email", "provider_user_id", "user__username", "user__email")
    readonly_fields = ("provider", "provider_user_id", "extra_data", "created_at", "updated_at")


admin.site.register(CustomUser, UserAgentAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Access)

admin.site.register(SocialAccount, SocialAccountAdmin)
