from django.contrib import admin

from dealio.apps.accounts.models import CustomUser, Access, Role, TokenBlacklist


class UserAgentAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'role')


class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_accesses',)

    def display_accesses(self, obj):
        return ', '.join([str(access) for access in obj.accesses.all()])

    display_accesses.short_description = 'Accesses'


admin.site.register(CustomUser, UserAgentAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Access)
admin.site.register(TokenBlacklist)
