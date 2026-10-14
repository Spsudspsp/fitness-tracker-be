from rest_framework.throttling import UserRateThrottle


class AIGenerationThrottle(UserRateThrottle):
    scope = 'ai_generation'
