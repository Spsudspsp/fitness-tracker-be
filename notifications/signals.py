from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from ai.signals import training_program_generation_succeeded, training_program_generation_failed
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

@receiver(training_program_generation_succeeded)
def create_training_program_generation_success_notification(sender, user, program, **kwargs):
    Notification.objects.create(
        user=user,
        type=NotificationCategory.SYSTEM,
        title='Training program generation done',
        content=f"Your training program '{program.name}' has finished generating successfully.",
    )

@receiver(training_program_generation_failed)
def create_training_program_generation_fail_notification(sender, user, **kwargs):
    Notification.objects.create(
        user=user,
        type=NotificationCategory.SYSTEM,
        title='Training program generation failed',
        content='We could not generate your training program. Please try again later or attempt with a different AI provider.',
    )
