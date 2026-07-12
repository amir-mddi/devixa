from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class ActiveUserJWTAuthentication(JWTAuthentication):
    """Reject soft-deleted users even when an old access token is still valid."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not user.is_active or getattr(user, "is_deleted", False):
            raise AuthenticationFailed("User is inactive.", code="user_inactive")
        return user
