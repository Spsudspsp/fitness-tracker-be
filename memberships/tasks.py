from celery import shared_task
from django.utils import timezone
from memberships.models import Membership


@shared_task
def expire_memberships():
    now = timezone.now()

    updated = Membership.objects.active().filter(expiration_date__lte=now).expire()

    return updated