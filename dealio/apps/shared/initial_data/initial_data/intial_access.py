from django.core.cache import cache


class InitialAccessCache:
    list_of_accesses = [
        "admin|UserSignUpViewSet|post|any",
        "admin|UsersViewSet|get|any",
        "admin|UsersViewSet|delete|any",
        "admin|UsersViewSet|put|any",
        "admin|PermissionViewSet|get|any",
        "admin|ChangePasswordView|put|any",
        "admin|AccessViewSet|delete|any",
        "admin|AccessViewSet|put|any",
        "admin|AccessViewSet|post|any",
        "admin|AccessViewSet|get|any",
        "admin|RoleViewSet|delete|any",
        "admin|RoleViewSet|get|any",
        "admin|RoleViewSet|post|any",
        "admin|RoleViewSet|put|any",
        "admin|UserSearchViewSet|get|any",
        "admin|LogoutView|post|any",

    ]

    @staticmethod
    def initial_accesses():
        cache.set('initial_access_list', InitialAccessCache.list_of_accesses, timeout=None)
        return cache.get('initial_access_list', [])
