import uuid

from django.conf import settings
from django.db import models


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Usage(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    used = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DailyUsage(Usage):
    date = models.DateField()

    class Meta:
        abstract = True


class TimeframeUsage(Usage):
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    class Meta:
        abstract = True
