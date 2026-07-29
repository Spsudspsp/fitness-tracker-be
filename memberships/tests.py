from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from memberships.models import Gym, Membership, MembershipStatus
from memberships.serializers import MembershipSerializer


User = get_user_model()


class MembershipBusinessTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='alex',
            email='alex@example.com',
            password='password',
        )
        self.other_user = User.objects.create_user(
            username='sam',
            email='sam@example.com',
            password='password',
        )
        self.client.force_authenticate(self.user)

        self.gym = Gym.objects.create(
            name='Downtown Strength',
            location='Main Street',
            description='Strength gym',
        )
        self.other_gym = Gym.objects.create(
            name='Other Gym',
            location='Side Street',
            description='Private gym',
        )

    def build_membership(self, user=None, gym=None, start_date=date(2026, 1, 31), months=1):
        membership = Membership(
            user=user or self.user,
            gym=gym or self.gym,
            start_date=start_date,
        )
        membership.set_dates(duration_months=months)
        return membership

    def test_create_membership_sets_owner_and_derived_dates(self):
        response = self.client.post(
            reverse('membership-list'),
            {
                'gym': str(self.gym.id),
                'start_date': '2026-01-31',
                'duration_months': 1,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        membership = Membership.objects.get()
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.gym, self.gym)
        self.assertEqual(membership.start_date, date(2026, 1, 31))
        self.assertEqual(membership.expiration_date, date(2026, 2, 28))
        self.assertEqual(membership.notify_at, date(2026, 2, 23))
        self.assertEqual(membership.status, MembershipStatus.ACTIVE)

    def test_create_requires_duration_months_because_duration_is_not_stored(self):
        serializer = MembershipSerializer(
            data={
                'gym': str(self.gym.id),
                'start_date': '2026-01-31',
            },
            context={'request': self.client.request().wsgi_request},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('duration_months', serializer.errors)

    def test_user_cannot_have_two_memberships_for_same_gym(self):
        self.build_membership()

        with self.assertRaises(IntegrityError):
            self.build_membership(start_date=date(2026, 3, 1))

    def test_different_users_can_have_memberships_for_same_gym(self):
        self.build_membership(user=self.user)
        other_membership = self.build_membership(user=self.other_user)

        self.assertEqual(other_membership.user, self.other_user)
        self.assertEqual(other_membership.gym, self.gym)

    def test_membership_queryset_is_limited_to_request_user(self):
        own_membership = self.build_membership(user=self.user)
        self.build_membership(user=self.other_user, gym=self.other_gym)

        response = self.client.get(reverse('membership-list'))

        returned_ids = {item['id'] for item in response.data}
        self.assertEqual(returned_ids, {str(own_membership.id)})

    def test_cancel_marks_membership_canceled_and_removes_notification_date(self):
        membership = self.build_membership()

        response = self.client.post(reverse('membership-cancel', args=[membership.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.CANCELED)
        self.assertIsNone(membership.notify_at)

    def test_cancel_does_not_affect_another_users_membership(self):
        membership = self.build_membership(user=self.other_user)

        response = self.client.post(reverse('membership-cancel', args=[membership.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.ACTIVE)
        self.assertEqual(membership.notify_at, date(2026, 2, 23))

    def test_renew_active_membership_extends_from_current_expiration_date(self):
        membership = self.build_membership(start_date=date(2026, 1, 31), months=1)

        response = self.client.post(
            reverse('membership-renew', args=[membership.id]),
            {'duration_months': 2},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.ACTIVE)
        self.assertEqual(membership.start_date, date(2026, 1, 31))
        self.assertEqual(membership.expiration_date, date(2026, 4, 28))
        self.assertEqual(membership.notify_at, date(2026, 4, 23))

    def test_renew_canceled_membership_reactivates_and_sets_notification_date(self):
        membership = self.build_membership(start_date=date(2026, 1, 31), months=1)
        membership.set_status_canceled()
        membership.save()

        response = self.client.post(
            reverse('membership-renew', args=[membership.id]),
            {'duration_months': 2},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.ACTIVE)
        self.assertEqual(membership.expiration_date, date(2026, 3, 31))
        self.assertEqual(membership.notify_at, date(2026, 3, 26))

    def test_non_active_memberships_cannot_keep_notification_dates(self):
        membership = self.build_membership()
        membership.status = MembershipStatus.EXPIRED

        with self.assertRaises(IntegrityError):
            membership.save()
