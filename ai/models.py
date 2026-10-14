from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from ai.exceptions import AIUsageLimitExceeded
from utils.models import UUIDModel, DailyUsage


DAILY_USAGE_LIMIT = 5

User = get_user_model()


class AIUsage(DailyUsage):
    model = models.CharField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'date'],
                name='ai_usage_unique_user_date'
            )
        ]


def consume_ai_usage(user_id):
    usage, _ = AIUsage.objects.select_for_update().get_or_create(user_id=user_id, date=timezone.localdate())

    if usage.used == DAILY_USAGE_LIMIT:
        raise AIUsageLimitExceeded()

    usage.used += 1
    usage.save(
        update_fields=['used', 'updated_at']
    )

    return usage