from django.contrib.auth import get_user_model
from django.db import models

from utils.models import UUIDModel

User = get_user_model()


class UserNotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')

    membership_in_app = models.BooleanField(default=True)


class NotificationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def for_users(self, users):
        return self.filter(user__in=users)

    def unread(self):
        return self.filter(read_at=None)

    def read(self):
        return self.exclude(read_at=None)


class NotificationCategory(models.TextChoices):
    MEMBERSHIP = 'membership', 'Membership'
    SECURITY = 'security', 'Security'
    SYSTEM = 'system', 'System'
    ADMIN = 'admin', 'Admin'


class Notification(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=10, choices=NotificationCategory.choices)
    title = models.CharField(max_length=255)
    content = models.TextField()
    deduplication_key = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ['-created']

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'deduplication_key'],
                condition=models.Q(deduplication_key__isnull=False),
                name='unique_notification_event_per_user',
            )
        ]
