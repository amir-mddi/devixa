
class InitializerData:
    role_data = [
        {
            "name": "کاربر سیستم",
            "symbol": "user",
            "accesses": []
        },
        {
            "name": "ادمین سیستم",
            "symbol": "admin",
            "accesses": [
                "UserSignUpViewSet|post|any",
                "UsersViewSet|get|any",
                "UsersViewSet|delete|any",
                "UsersViewSet|put|any",
                "PermissionViewSet|get|any",
                "ChangePasswordView|put|any",
                "AccessViewSet|delete|any",
                "AccessViewSet|put|any",
                "AccessViewSet|post|any",
                "AccessViewSet|get|any",
                "RoleViewSet|delete|any",
                "RoleViewSet|get|any",
                "RoleViewSet|post|any",
                "RoleViewSet|put|any",
                "UserSearchViewSet|get|any",
                "LogoutView|post|any",
            ]
        },
    ]