from celery import shared_task
from django.utils import timezone

from memberships.models import Membership
from notifications.models import Notification, NotificationCategory


@shared_task
def send_membership_expiring_soon_notification():
    now = timezone.localdate()
    expiring_soon = Membership.objects.active().filter(
        user__notification_preference__membership_in_app=True,
        notify_at=now
    ).select_related('gym')

    notifications = []

    for membership in expiring_soon:
        notification = Notification(
            user=membership.user_id,
            type=NotificationCategory.MEMBERSHIP,
            title='Membership expiring soon',
            content=f'Your membership at {membership.gym.name} will expire soon ({membership.expiration_date})',
            deduplication_key=f'membership-expiring-soon:{membership.id}'
        )

        notifications.append(notification)

    Notification.objects.bulk_create(notifications, ignore_conflicts=True)
