import uuid
from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Usage(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
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