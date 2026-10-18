from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ai.exceptions import AIUsageLimitExceeded
from ai.models import DAILY_USAGE_LIMIT, AIUsage, consume_ai_usage
from ai.serializers import PlanRequestSerializer
from ai.tasks import (
    TRAINING_PROGRAM_GENERATION_URL,
    create_training_program,
    generate_training_program,
    process_request_data,
)
from exercises.models import Equipment, Exercise, MuscleGroup
from workouts.models import Day, Program, ProgramWorkout, Workout, WorkoutExercise

User = get_user_model()


class PlanRequestSerializerTests(SimpleTestCase):
    def setUp(self):
        self.data = {
            'provider': 'openai',
            'experience_level': 'beginner',
            'goal_weight': '75.50',
            'notes': 'Focus on strength.',
            'days_per_week': 3,
        }

    def test_valid_request_converts_weight_to_decimal(self):
        serializer = PlanRequestSerializer(data=self.data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['goal_weight'], Decimal('75.50'))
        self.assertEqual(serializer.validated_data['days_per_week'], 3)

    def test_all_fields_are_required(self):
        for field in self.data:
            with self.subTest(field=field):
                data = self.data.copy()
                del data[field]
                serializer = PlanRequestSerializer(data=data)

                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_rejects_invalid_field_values(self):
        invalid_values = {
            'provider': ['', None],
            'experience_level': ['', None],
            'goal_weight': ['invalid', '1000.00', '75.555', None],
            'notes': ['', ' ' * 5, 'a' * 2001, None],
            'days_per_week': [0, 8, 1.5, 'invalid', None],
        }

        for field, values in invalid_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    serializer = PlanRequestSerializer(data={**self.data, field: value})

                    self.assertFalse(serializer.is_valid())
                    self.assertIn(field, serializer.errors)

    def test_accepts_day_and_notes_length_boundaries(self):
        for days in [1, 7]:
            with self.subTest(days=days):
                serializer = PlanRequestSerializer(data={**self.data, 'days_per_week': days, 'notes': 'a' * 2000})

                self.assertTrue(serializer.is_valid(), serializer.errors)


class AIUsageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='alex',
            email='alex@example.com',
            password='password',
        )
        self.today = date(2026, 10, 18)
        localdate_patch = patch('ai.models.timezone.localdate', return_value=self.today)
        localdate_patch.start()
        self.addCleanup(localdate_patch.stop)

    def test_first_use_creates_daily_usage(self):
        usage = consume_ai_usage(self.user.id)

        usage.refresh_from_db()
        self.assertEqual(usage.user, self.user)
        self.assertEqual(usage.date, self.today)
        self.assertEqual(usage.used, 1)

    def test_existing_daily_usage_is_incremented(self):
        usage = AIUsage.objects.create(user=self.user, date=self.today, used=2)

        result = consume_ai_usage(self.user.id)

        usage.refresh_from_db()
        self.assertEqual(result.pk, usage.pk)
        self.assertEqual(usage.used, 3)
        self.assertEqual(AIUsage.objects.count(), 1)

    def test_last_allowed_use_reaches_limit(self):
        AIUsage.objects.create(user=self.user, date=self.today, used=DAILY_USAGE_LIMIT - 1)

        usage = consume_ai_usage(self.user.id)

        self.assertEqual(usage.used, DAILY_USAGE_LIMIT)

    def test_daily_limit_rejects_usage_without_incrementing(self):
        usage = AIUsage.objects.create(user=self.user, date=self.today, used=DAILY_USAGE_LIMIT)

        with self.assertRaises(AIUsageLimitExceeded):
            consume_ai_usage(self.user.id)

        usage.refresh_from_db()
        self.assertEqual(usage.used, DAILY_USAGE_LIMIT)
        self.assertEqual(AIUsage.objects.count(), 1)

    def test_previous_days_usage_does_not_consume_todays_limit(self):
        previous_usage = AIUsage.objects.create(
            user=self.user,
            date=self.today - timedelta(days=1),
            used=DAILY_USAGE_LIMIT,
        )

        usage = consume_ai_usage(self.user.id)

        previous_usage.refresh_from_db()
        self.assertEqual(usage.date, self.today)
        self.assertEqual(usage.used, 1)
        self.assertEqual(previous_usage.used, DAILY_USAGE_LIMIT)

    def test_daily_limit_is_separate_for_each_user(self):
        AIUsage.objects.create(user=self.user, date=self.today, used=DAILY_USAGE_LIMIT)
        other_user = User.objects.create_user(
            username='sam',
            email='sam@example.com',
            password='password',
        )

        usage = consume_ai_usage(other_user.id)

        self.assertEqual(usage.user, other_user)
        self.assertEqual(usage.used, 1)

    def test_user_cannot_have_duplicate_usage_for_same_day(self):
        AIUsage.objects.create(user=self.user, date=self.today)

        with self.assertRaises(IntegrityError), transaction.atomic():
            AIUsage.objects.create(user=self.user, date=self.today)

        self.assertEqual(AIUsage.objects.count(), 1)


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class AITrainingProgramAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='alex',
            email='alex@example.com',
            password='password',
        )
        self.client.force_authenticate(self.user)
        self.data = {
            'provider': 'openai',
            'experience_level': 'beginner',
            'goal_weight': '75.50',
            'notes': 'Focus on strength.',
            'days_per_week': 3,
        }
        cache.clear()
        self.addCleanup(cache.clear)
        delay_patch = patch('ai.views.generate_training_program.delay')
        self.delay = delay_patch.start()
        self.addCleanup(delay_patch.stop)

    def test_valid_request_consumes_usage_and_queues_task_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(reverse('training-plan'), self.data, format='json')
            self.delay.assert_not_called()

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(len(callbacks), 1)
        self.delay.assert_called_once_with({**self.data, 'user_id': self.user.id})
        usage = AIUsage.objects.get()
        self.assertEqual(usage.user, self.user)
        self.assertEqual(usage.date, timezone.localdate())
        self.assertEqual(usage.used, 1)

    def test_request_cannot_override_authenticated_user(self):
        other_user = User.objects.create_user(
            username='sam',
            email='sam@example.com',
            password='password',
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('training-plan'),
                {**self.data, 'user_id': str(other_user.id)},
                format='json',
            )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.delay.assert_called_once_with({**self.data, 'user_id': self.user.id})
        self.assertEqual(AIUsage.objects.get().user, self.user)

    def test_invalid_request_does_not_consume_usage_or_queue_task(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(
                reverse('training-plan'),
                {**self.data, 'days_per_week': 8},
                format='json',
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('days_per_week', response.data)
        self.assertFalse(AIUsage.objects.exists())
        self.assertEqual(callbacks, [])
        self.delay.assert_not_called()

    def test_unauthenticated_requests_are_rejected(self):
        self.client.force_authenticate(user=None)

        for url_name in ['training-plan', 'nutrition-plan']:
            with self.subTest(url_name=url_name), self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(reverse(url_name), self.data, format='json')

                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertFalse(AIUsage.objects.exists())
        self.delay.assert_not_called()

    def test_daily_limit_returns_429_without_queuing_task(self):
        usage = AIUsage.objects.create(user=self.user, date=timezone.localdate(), used=DAILY_USAGE_LIMIT)

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(reverse('training-plan'), self.data, format='json')

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(str(response.data['detail']), 'Daily AI generation limit exceeded.')
        self.assertEqual(response.data['detail'].code, 'ai_usage_limit_reached')
        usage.refresh_from_db()
        self.assertEqual(usage.used, DAILY_USAGE_LIMIT)
        self.assertEqual(callbacks, [])
        self.delay.assert_not_called()

    def test_repeated_request_is_throttled_without_consuming_extra_usage(self):
        with self.captureOnCommitCallbacks(execute=True):
            first_response = self.client.post(reverse('training-plan'), self.data, format='json')
            second_response = self.client.post(reverse('training-plan'), self.data, format='json')

        self.assertEqual(first_response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(second_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Retry-After', second_response)
        self.assertEqual(AIUsage.objects.get().used, 1)
        self.delay.assert_called_once()

    def test_throttle_allows_request_after_one_minute(self):
        with patch('ai.throttles.AIGenerationThrottle.timer', side_effect=[0, 60]):
            with self.captureOnCommitCallbacks(execute=True):
                first_response = self.client.post(reverse('training-plan'), self.data, format='json')
                second_response = self.client.post(reverse('training-plan'), self.data, format='json')

        self.assertEqual(first_response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(second_response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(AIUsage.objects.get().used, 2)
        self.assertEqual(self.delay.call_count, 2)

    def test_throttle_is_separate_for_each_user(self):
        other_user = User.objects.create_user(
            username='sam',
            email='sam@example.com',
            password='password',
        )

        with self.captureOnCommitCallbacks(execute=True):
            first_response = self.client.post(reverse('training-plan'), self.data, format='json')
            self.client.force_authenticate(other_user)
            second_response = self.client.post(reverse('training-plan'), self.data, format='json')

        self.assertEqual(first_response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(second_response.status_code, status.HTTP_202_ACCEPTED)
        self.assertCountEqual(
            AIUsage.objects.values_list('user_id', 'used'),
            [(self.user.id, 1), (other_user.id, 1)],
        )
        self.assertEqual(self.delay.call_count, 2)

    def test_rolled_back_request_does_not_consume_usage_or_queue_task(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            with transaction.atomic():
                response = self.client.post(reverse('training-plan'), self.data, format='json')
                transaction.set_rollback(True)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertFalse(AIUsage.objects.exists())
        self.assertEqual(callbacks, [])
        self.delay.assert_not_called()


class TrainingProgramGenerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='alex',
            email='alex@example.com',
            password='password',
        )
        profile = self.user.profile
        profile.weight = Decimal('80.25')
        profile.height = Decimal('180.50')
        profile.birth_date = date(2000, 1, 1)
        profile.save()
        self.squat = Exercise.objects.create(
            name='Squat',
            description='Barbell squat',
            muscle_groups=[MuscleGroup.QUADRICEPS, MuscleGroup.GLUTES],
            equipment=[Equipment.BARBELL, Equipment.SQUAT_RACK],
        )
        self.bench_press = Exercise.objects.create(
            name='Bench press',
            description='Flat barbell bench press',
            muscle_groups=[MuscleGroup.CHEST, MuscleGroup.TRICEPS],
            equipment=[Equipment.BARBELL, Equipment.BENCH],
        )
        self.request_data = {
            'provider': 'openai',
            'experience_level': 'beginner',
            'goal_weight': '75.50',
            'notes': 'Focus on strength.',
            'days_per_week': 2,
        }
        self.program_data = {
            'name': 'Strength plan',
            'description': 'Two days of strength training.',
            'workouts': [
                {
                    'name': 'Full body A',
                    'day': Day.MON,
                    'exercises': [
                        {'exercise': str(self.squat.id), 'sets': 3, 'reps': 5},
                        {'exercise': str(self.bench_press.id), 'sets': 4, 'reps': 8},
                    ],
                },
                {
                    'name': 'Full body B',
                    'day': Day.FRI,
                    'exercises': [
                        {'exercise': str(self.squat.id), 'sets': 2, 'reps': 10},
                    ],
                },
            ],
        }

    def test_request_data_includes_profile_and_available_exercises(self):
        with patch('users.models.Profile.get_age', return_value=26):
            data = process_request_data(self.request_data.copy(), self.user)

        self.assertEqual(data['user_weight'], 80.25)
        self.assertEqual(data['goal_weight'], 75.5)
        self.assertEqual(data['user_height'], 180.5)
        self.assertEqual(data['user_age'], 26)
        self.assertIsInstance(data['goal_weight'], float)
        for field in ['provider', 'experience_level', 'notes', 'days_per_week']:
            self.assertEqual(data[field], self.request_data[field])
        self.assertCountEqual(
            data['available_exercises'],
            [
                {
                    'id': str(self.squat.id),
                    'name': 'Squat',
                    'description': 'Barbell squat',
                    'muscle_groups': [MuscleGroup.QUADRICEPS, MuscleGroup.GLUTES],
                    'equipment': [Equipment.BARBELL, Equipment.SQUAT_RACK],
                },
                {
                    'id': str(self.bench_press.id),
                    'name': 'Bench press',
                    'description': 'Flat barbell bench press',
                    'muscle_groups': [MuscleGroup.CHEST, MuscleGroup.TRICEPS],
                    'equipment': [Equipment.BARBELL, Equipment.BENCH],
                },
            ],
        )

    def test_request_data_with_no_available_exercises(self):
        Exercise.objects.all().delete()

        data = process_request_data(self.request_data.copy(), self.user)

        self.assertEqual(data['available_exercises'], [])

    def test_create_program_persists_workouts_schedule_and_exercises(self):
        program = create_training_program(self.user, self.program_data)

        program.refresh_from_db()
        self.assertEqual(program.user, self.user)
        self.assertEqual(program.name, 'Strength plan')
        self.assertEqual(program.description, 'Two days of strength training.')
        self.assertEqual(Program.objects.count(), 1)
        self.assertEqual(Workout.objects.count(), 2)
        self.assertCountEqual(
            program.programworkout_set.values_list('workout__name', 'workout__user_id', 'day'),
            [
                ('Full body A', self.user.id, Day.MON),
                ('Full body B', self.user.id, Day.FRI),
            ],
        )
        self.assertCountEqual(
            WorkoutExercise.objects.values_list('workout__name', 'exercise_id', 'sets', 'reps'),
            [
                ('Full body A', self.squat.id, 3, 5),
                ('Full body A', self.bench_press.id, 4, 8),
                ('Full body B', self.squat.id, 2, 10),
            ],
        )
        self.assertEqual(Exercise.objects.count(), 2)

    def test_missing_exercise_field_rolls_back_program(self):
        del self.program_data['workouts'][1]['exercises'][0]['reps']

        with self.assertRaises(KeyError):
            create_training_program(self.user, self.program_data)

        self.assertFalse(Program.objects.exists())
        self.assertFalse(Workout.objects.exists())
        self.assertFalse(WorkoutExercise.objects.exists())
        self.assertFalse(ProgramWorkout.objects.exists())

    def test_database_failure_rolls_back_program_and_workouts(self):
        self.program_data['workouts'][1]['exercises'][0]['sets'] = -1

        with self.assertRaises(IntegrityError):
            create_training_program(self.user, self.program_data)

        self.assertFalse(Program.objects.exists())
        self.assertFalse(Workout.objects.exists())
        self.assertFalse(WorkoutExercise.objects.exists())
        self.assertFalse(ProgramWorkout.objects.exists())

    def test_generation_calls_service_and_signals_success(self):
        with (
            patch('ai.tasks.requests.post') as post,
            patch('ai.tasks.config', return_value='test-service-key'),
            patch('ai.tasks.training_program_generation_succeeded.send') as succeeded,
            patch('ai.tasks.training_program_generation_failed.send') as failed,
        ):
            post.return_value.json.return_value = self.program_data

            generate_training_program.run({**self.request_data, 'user_id': self.user.id})

        post.assert_called_once()
        self.assertEqual(post.call_args.args, (TRAINING_PROGRAM_GENERATION_URL,))
        self.assertEqual(
            post.call_args.kwargs['headers'],
            {'Content-Type': 'application/json', 'x-service-key': 'test-service-key'},
        )
        self.assertEqual(post.call_args.kwargs['timeout'], (5, 60))
        payload = post.call_args.kwargs['json']
        self.assertNotIn('user_id', payload)
        self.assertEqual(payload['user_weight'], 80.25)
        self.assertEqual(payload['goal_weight'], 75.5)
        self.assertEqual(payload['provider'], 'openai')
        post.return_value.raise_for_status.assert_called_once_with()
        program = Program.objects.get()
        self.assertEqual(program.user, self.user)
        self.assertEqual(program.workouts.count(), 2)
        succeeded.assert_called_once_with(sender=Program, user=self.user, program=program)
        failed.assert_not_called()

    def test_service_errors_signal_failure_and_are_reraised(self):
        errors = [
            requests.Timeout('Timed out'),
            requests.ConnectionError('Unavailable'),
            requests.HTTPError('Bad gateway'),
        ]

        for error in errors:
            with (
                self.subTest(error=type(error).__name__),
                patch('ai.tasks.requests.post') as post,
                patch('ai.tasks.training_program_generation_succeeded.send') as succeeded,
                patch('ai.tasks.training_program_generation_failed.send') as failed,
                self.assertLogs('ai.tasks', level='ERROR') as logs,
            ):
                if isinstance(error, requests.HTTPError):
                    post.return_value.raise_for_status.side_effect = error
                else:
                    post.side_effect = error

                with self.assertRaises(type(error)) as raised:
                    generate_training_program.run({**self.request_data, 'user_id': self.user.id})

                self.assertIs(raised.exception, error)
                failed.assert_called_once_with(sender=Program, user=self.user)
                succeeded.assert_not_called()
                self.assertFalse(Program.objects.exists())
                self.assertFalse(Workout.objects.exists())
                if isinstance(error, requests.Timeout):
                    self.assertIn('timed out', logs.output[0])
                if isinstance(error, requests.HTTPError):
                    post.return_value.json.assert_not_called()

    def test_invalid_json_signals_failure_without_creating_program(self):
        error = requests.exceptions.JSONDecodeError('Invalid JSON', '<html>', 0)
        with (
            patch('ai.tasks.requests.post') as post,
            patch('ai.tasks.training_program_generation_succeeded.send') as succeeded,
            patch('ai.tasks.training_program_generation_failed.send') as failed,
            self.assertLogs('ai.tasks', level='ERROR'),
        ):
            post.return_value.json.side_effect = error

            with self.assertRaises(requests.exceptions.JSONDecodeError):
                generate_training_program.run({**self.request_data, 'user_id': self.user.id})

        self.assertFalse(Program.objects.exists())
        failed.assert_called_once_with(sender=Program, user=self.user)
        succeeded.assert_not_called()

    def test_malformed_service_data_rolls_back_and_signals_failure(self):
        del self.program_data['workouts'][1]['exercises'][0]['exercise']
        with (
            patch('ai.tasks.requests.post') as post,
            patch('ai.tasks.training_program_generation_succeeded.send') as succeeded,
            patch('ai.tasks.training_program_generation_failed.send') as failed,
            self.assertLogs('ai.tasks', level='ERROR'),
        ):
            post.return_value.json.return_value = self.program_data

            with self.assertRaises(KeyError):
                generate_training_program.run({**self.request_data, 'user_id': self.user.id})

        self.assertFalse(Program.objects.exists())
        self.assertFalse(Workout.objects.exists())
        self.assertFalse(WorkoutExercise.objects.exists())
        self.assertFalse(ProgramWorkout.objects.exists())
        failed.assert_called_once_with(sender=Program, user=self.user)
        succeeded.assert_not_called()

    def test_incomplete_profile_signals_failure_without_calling_service(self):
        self.user.profile.weight = None
        self.user.profile.save(update_fields=['weight'])
        with (
            patch('ai.tasks.requests.post') as post,
            patch('ai.tasks.training_program_generation_succeeded.send') as succeeded,
            patch('ai.tasks.training_program_generation_failed.send') as failed,
            self.assertLogs('ai.tasks', level='ERROR'),
        ):
            with self.assertRaises(TypeError):
                generate_training_program.run({**self.request_data, 'user_id': self.user.id})

        post.assert_not_called()
        self.assertFalse(Program.objects.exists())
        failed.assert_called_once_with(sender=Program, user=self.user)
        succeeded.assert_not_called()

    def test_missing_user_does_not_call_service_or_send_signals(self):
        with (
            patch('ai.tasks.requests.post') as post,
            patch('ai.tasks.training_program_generation_succeeded.send') as succeeded,
            patch('ai.tasks.training_program_generation_failed.send') as failed,
        ):
            with self.assertRaises(User.DoesNotExist):
                generate_training_program.run({**self.request_data, 'user_id': uuid4()})

        post.assert_not_called()
        succeeded.assert_not_called()
        failed.assert_not_called()
        self.assertFalse(Program.objects.exists())
