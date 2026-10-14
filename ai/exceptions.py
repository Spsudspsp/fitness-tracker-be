from rest_framework import status
from rest_framework.exceptions import APIException


class AIUsageLimitExceeded(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Daily AI generation limit exceeded.'
    default_code = 'ai_usage_limit_reached'
