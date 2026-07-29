from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from exercises.models import Equipment, Exercise, MuscleGroup
from workouts.models import Day, Program, ProgramWorkout, Workout, WorkoutExercise


User = get_user_model()


class WorkoutAPITests(APITestCase):
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
        self.row = Exercise.objects.create(
            name='Row',
            description='Cable row',
            muscle_groups=[MuscleGroup.BACK],
            equipment=[Equipment.CABLE],
        )

    def test_create_workout_creates_exercise_plan_for_authenticated_user(self):
        response = self.client.post(
            reverse('workout-list'),
            {
                'exercises': [
                    {'exercise': str(self.squat.id), 'sets': 3, 'reps': 5},
                    {'exercise': str(self.bench_press.id), 'sets': 4, 'reps': 8},
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        workout = Workout.objects.get()
        self.assertEqual(workout.user, self.user)
        self.assertCountEqual(
            WorkoutExercise.objects.values_list('exercise_id', 'sets', 'reps'),
            [
                (self.squat.id, 3, 5),
                (self.bench_press.id, 4, 8),
            ],
        )
        self.assertEqual(response.data['estimated_working_duration'], 14)
        self.assertEqual(response.data['estimated_resting_duration'], 10)
        self.assertEqual(response.data['estimated_total_duration'], 24)
        self.assertEqual(response.data['exercises'][0]['exercise']['name'], 'Squat')

    def test_update_workout_replaces_exercise_plan(self):
        workout = Workout.objects.create(user=self.user)
        WorkoutExercise.objects.create(
            workout=workout,
            exercise=self.squat,
            sets=3,
            reps=5,
        )
        WorkoutExercise.objects.create(
            workout=workout,
            exercise=self.bench_press,
            sets=4,
            reps=8,
        )

        response = self.client.patch(
            reverse('workout-detail', args=[workout.id]),
            {
                'exercises': [
                    {'exercise': str(self.row.id), 'sets': 2, 'reps': 12},
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            list(workout.workoutexercise_set.values_list('exercise_id', 'sets', 'reps')),
            [(self.row.id, 2, 12)],
        )
        self.assertEqual(response.data['estimated_working_duration'], 4)
        self.assertEqual(response.data['estimated_resting_duration'], 2)
        self.assertEqual(response.data['estimated_total_duration'], 6)

    def test_workout_list_is_limited_to_request_user(self):
        own_workout = Workout.objects.create(user=self.user)
        other_workout = Workout.objects.create(user=self.other_user)
        WorkoutExercise.objects.create(
            workout=own_workout,
            exercise=self.squat,
            sets=3,
            reps=5,
        )
        WorkoutExercise.objects.create(
            workout=other_workout,
            exercise=self.bench_press,
            sets=4,
            reps=8,
        )

        response = self.client.get(reverse('workout-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(own_workout.id))

    def test_create_program_creates_scheduled_workouts_for_authenticated_user(self):
        monday_workout = Workout.objects.create(user=self.user)
        friday_workout = Workout.objects.create(user=self.user)
        WorkoutExercise.objects.create(
            workout=monday_workout,
            exercise=self.squat,
            sets=3,
            reps=5,
        )
        WorkoutExercise.objects.create(
            workout=friday_workout,
            exercise=self.bench_press,
            sets=4,
            reps=8,
        )

        response = self.client.post(
            reverse('program-list'),
            {
                'workouts': [
                    {'workout': str(monday_workout.id), 'day': Day.MON},
                    {'workout': str(friday_workout.id), 'day': Day.FRI},
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        program = Program.objects.get()
        self.assertEqual(program.user, self.user)
        self.assertCountEqual(
            ProgramWorkout.objects.values_list('workout_id', 'day'),
            [
                (monday_workout.id, Day.MON),
                (friday_workout.id, Day.FRI),
            ],
        )
        self.assertEqual(response.data['workouts'][0]['workout']['id'], str(monday_workout.id))
        self.assertEqual(response.data['workouts'][0]['workout']['estimated_total_duration'], 10)

    def test_program_list_is_limited_to_request_user(self):
        own_program = Program.objects.create(user=self.user)
        other_program = Program.objects.create(user=self.other_user)
        own_workout = Workout.objects.create(user=self.user)
        other_workout = Workout.objects.create(user=self.other_user)
        ProgramWorkout.objects.create(program=own_program, workout=own_workout, day=Day.MON)
        ProgramWorkout.objects.create(program=other_program, workout=other_workout, day=Day.TUE)
        WorkoutExercise.objects.create(
            workout=own_workout,
            exercise=self.squat,
            sets=3,
            reps=5,
        )
        WorkoutExercise.objects.create(
            workout=other_workout,
            exercise=self.bench_press,
            sets=4,
            reps=8,
        )

        response = self.client.get(reverse('program-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(own_program.id))
