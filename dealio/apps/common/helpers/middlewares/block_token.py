from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import UntypedToken


class BlockedTokenMiddleware:
    """Legacy middleware kept safe for deployments that still enable it.

    Signature/expiry validation is delegated to SimpleJWT. The middleware does
    not log bearer tokens and does not maintain a second plaintext-token cache.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            try:
                UntypedToken(token)
            except TokenError:
                return JsonResponse({"detail": "Invalid or expired token."}, status=401)
        return self.get_response(request)
