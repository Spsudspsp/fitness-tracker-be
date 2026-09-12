from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q

from memberships.signals import memberships_expired
from utils.models import UUIDModel

User = get_user_model()


class Gym(UUIDModel):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class MembershipStatus(models.TextChoices):
    ACTIVE = ('active', 'ACTIVE')
    EXPIRED = ('expired', 'EXPIRED')
    CANCELED = ('canceled', 'CANCELED')


class MembershipQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=MembershipStatus.ACTIVE)

    def expired(self):
        return self.filter(status=MembershipStatus.EXPIRED)

    def canceled(self):
        return self.filter(status=MembershipStatus.CANCELED)

    def expire(self):
        expired = self.update(status=MembershipStatus.EXPIRED)
        memberships_expired.send(sender=self.model, memberships=expired)
        return expired


class Membership(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    start_date = models.DateField(blank=True)
    expiration_date = models.DateField()
    notify_at = models.DateField(null=True)
    status = models.CharField(
        max_length=10,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(status=MembershipStatus.ACTIVE) | Q(notify_at__isnull=True),
                name='active_membership_requires_notify_at',
            ),
            models.UniqueConstraint(fields=['gym', 'user'], name='unique_membership_gym_user'),
        ]

    objects = MembershipQuerySet.as_manager()

    @property
    def is_active(self):
        return self.status == MembershipStatus.ACTIVE

    @property
    def is_expired(self):
        return self.status == MembershipStatus.EXPIRED

    @property
    def is_canceled(self):
        return self.status == MembershipStatus.CANCELED

    @staticmethod
    def get_expiration_date(start_date, duration_months):
        return start_date + relativedelta(months=duration_months)

    @staticmethod
    def get_notification_date(expiration_date):
        return expiration_date - timedelta(days=5)

    def set_dates(self, start_date=None, duration_months=1):
        if start_date is not None:
            self.start_date = start_date
        if self.is_active and self.expiration_date:
            expiration_date = self.get_expiration_date(self.expiration_date, duration_months)
        else:
            expiration_date = self.get_expiration_date(self.start_date, duration_months)

        self.expiration_date = expiration_date
        self.notify_at = self.get_notification_date(self.expiration_date)
        self.set_status_active()

        self.save()

    def set_status_active(self):
        self.status = MembershipStatus.ACTIVE

    def set_status_canceled(self):
        self.status = MembershipStatus.CANCELED
        self.notify_at = None

    def set_status_expired(self):
        self.status = MembershipStatus.EXPIRED
