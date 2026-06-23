import logging

import jwt
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger("dealio")


class BlockedTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and 'Bearer' in auth_header:
            token = auth_header.split("Bearer ")[1]
            try:
                jwt_sign = jwt.decode(token, options={"verify_signature": False})
                user_id = jwt_sign.get('user_id')
            except jwt.exceptions.DecodeError as e:
                user_id = None
                logger.info(f"Token:{token}")
                logger.error(f"error occurred with detail when decoding jwt: {e}")
            access_token = cache.get(f"mock_service_user_access_token_with_id:{user_id}", None) if user_id else None
            if not (access_token and access_token == token):
                # return CommonJsonResponse(status_code=403, status=ResponseVO.failed,
                #                           message=ResponseVO.invalid_token_msg,
                #                           code=ResponseVO.invalid_token_code)
                return JsonResponse(data={"detail": "Token is expired"}, status=403)

        return self.get_response(request)
