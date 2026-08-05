from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import UserNotificationPreference

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_notification_preference(sender, instance, created, **kwargs):
    if created:
        UserNotificationPreference.objects.create(user=instance)
