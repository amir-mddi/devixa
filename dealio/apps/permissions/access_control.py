import logging

import jwt
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission

from dealio.apps.shared.initial_data.initial_data.intial_access import InitialAccessCache

logger = logging.getLogger("dealio")


class AccessLimitPermission(BasePermission):
    @classmethod
    def config(cls, request, view_name):
        user = request.user

        auth_header = request.headers.get("Authorization")

        if auth_header and "Bearer" in auth_header:
            token = auth_header.split("Bearer ")[1]
            jwt_sign = jwt.decode(token, options={"verify_signature": False})
            user_group = jwt_sign.get("role")
        else:
            user_group = ""

        pattern = f"{user_group}|{view_name}|{request.method.lower()}|"

        permissions = getattr(settings, "PERMISSIONS", None)

        if not permissions:
            permissions = InitialAccessCache.initial_accesses()
            settings.PERMISSIONS = permissions

        return user, pattern, permissions, user_group

    def has_permission(self, request, view):
        try:
            user, pattern, permissions, user_group = AccessLimitPermission.config(
                request,
                view.__class__.__name__,
            )

            if (
                user.is_active
                and user.is_authenticated
                and user_group
                and (
                    pattern + "any" in permissions
                    or pattern + "self" in permissions
                    or user.is_superuser
                )
            ):
                return True

        except ObjectDoesNotExist:
            logger.error(f"user:{user} with id:{user.id} does not exist")

        except Exception as e:
            logger.error(
                f"error occurred when check user have permission or not with detail:{e}"
            )

        return False

    @staticmethod
    def has_access_to_action(clz, request):
        user, pattern, permissions, user_group = AccessLimitPermission.config(
            request,
            clz.__class__.__name__,
        )

        if pattern + "any" in permissions or user.is_superuser:
            return True

        return False