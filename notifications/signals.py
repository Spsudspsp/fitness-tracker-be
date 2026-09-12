from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from memberships.signals import memberships_expired
from notifications.models import UserNotificationPreference, Notification, NotificationCategory

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_notification_preference(sender, instance, created, **kwargs):
    if created:
        UserNotificationPreference.objects.create(user=instance)


@receiver(memberships_expired)
def create_membership_expired_notification(sender, memberships, **kwargs):
    memberships = memberships.filter(
        user__notification_preference__membership_in_app=True
    ).select_related('user', 'gym')

    notifications = []

    for membership in memberships:
        notification = Notification(
            user=membership.user,
            type=NotificationCategory.MEMBERSHIP,
            title='Membership expired',
            content=f'Your membership at {membership.gym.name} has expired.',
        )
        notifications.append(notification)

    Notification.objects.bulk_create(notifications)