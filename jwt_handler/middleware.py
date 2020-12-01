import re
from enum import Enum

import jwt
from django.http.response import JsonResponse
from rest_framework import status

from config import config


def jwt_check_middleware(get_response):
    def middleware(request):

        ignore_check_urls = [
            r'^(\/)$',
            r'^(\/member\/login)$',
            r'^(\/member\/register)$',
            r'^(\/order\/complete\/)'
        ]

        # APIs do not require Token check
        for pattern in ignore_check_urls:
            if bool(re.search(pattern, request.path)):
                return get_response(request)

        try:
            auth = request.META.get('HTTP_AUTHORIZATION').split()
        except AttributeError:
            return JsonResponse({"message": JWTCheckErrorTypes.NO_AUTHENTICATE_HEADER.value},
                                status=status.HTTP_401_UNAUTHORIZED)

        if auth[0].lower() == 'token':
            try:
                payload = jwt.decode(
                    auth[1], config['SECRET_KEY'], algorithms=['HS256'])
                data = payload.get('data')
                request.META['TOKEN_PAYLOAD'] = data
                response = get_response(request)
                return response

            except jwt.ExpiredSignatureError:
                return JsonResponse({"message": JWTCheckErrorTypes.TOKEN_EXPIRED.value},
                                    status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return JsonResponse({"message": JWTCheckErrorTypes.INVALID_TOKEN.value},
                                    status=status.HTTP_401_UNAUTHORIZED)

        else:
            return JsonResponse({"message": JWTCheckErrorTypes.NOT_SUPPORT_AUTH_TYPE.value},
                                status=status.HTTP_401_UNAUTHORIZED)

    return middleware


class JWTCheckErrorTypes(Enum):
    NO_AUTHENTICATE_HEADER = 'No authenticate header'
    NOT_SUPPORT_AUTH_TYPE = 'Not support auth type'
    INVALID_TOKEN = 'Invalid token'
    TOKEN_EXPIRED = 'Token expired'
