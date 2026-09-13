from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from ai.signals import training_program_generated
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
    ).select_related('gym')

    notifications = []

    for membership in memberships:
        notification = Notification(
            user=membership.user_id,
            type=NotificationCategory.MEMBERSHIP,
            title='Membership expired',
            content=f'Your membership at {membership.gym.name} has expired.',
        )
        notifications.append(notification)

    Notification.objects.bulk_create(notifications)

@receiver(training_program_generated)
def create_training_program_generated_notification(sender, user, training_program, **kwargs):
    Notification.objects.create(
        user=user,
        type=NotificationCategory.SYSTEM,
        title='Training program',
        content='Your training program has finished generating successfully.',
    )