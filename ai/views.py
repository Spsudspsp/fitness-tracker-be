import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from exercises.models import Exercise
from exercises.serializers import ExerciseSerializer
from workouts.models import WorkoutExercise, Workout, ProgramWorkout, Program
from ai import serializers

User = get_user_model()


class AITrainingPlanView(APIView):
    TRAINING_PLAN_GENERATION_URL = f'{settings.AI_SERVICE_URL}/training_plans/generate'

    def post(self, request, *args, **kwargs):
        user = User.objects.select_related('profile').get(pk=request.user.pk)

        serializer = serializers.PlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        data['user'] = user
        data['ai_provider'] = self.request.POST.get('ai_provider', None)

        self.generate_training_plan(data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def generate_training_plan(self, data):
        user = data['user']
        provider = data['ai_provider']
        notes = data['notes']
        goal_weight = data['goal_weight']

        req = dict(
            provider=provider,
            age=data.profile.get_age(),
            weight_kg=float(user.profile.weight),
            height_cm=float(user.profile.height),
            goal_weight=goal_weight,
            notes=notes,
            experience_level='beginner',
            days_per_week=6,
            available_exercises=ExerciseSerializer(Exercise.objects.all(), many=True, context=dict(request=self.request)).data,
        )

        res = requests.post(
            self.TRAINING_PLAN_GENERATION_URL,
            json=req,
            headers={'Content-Type': 'application/json', 'x-service-key': settings.AI_SERVICE_KEY},
        )
        data = res.json()

        # program_name = data['name']
        # program_description = data['description']

        program = Program.objects.create(
            user=user,
        )

        workouts = data['workouts']

        workout_objs = []
        program_workout_objs = []
        workout_exercise_objs = []

        for workout in workouts:
            # workout_name = workout['name']
            workout_obj = Workout(
                user=user,
            )
            workout_objs.append(workout_obj)

            program_workout_obj = ProgramWorkout(
                workout=workout_obj,
                day=workout['day'],
                program=program
            )
            program_workout_objs.append(program_workout_obj)

            exercises = workout['exercises']

            for exercise in exercises:
                workout_exercise_obj = WorkoutExercise(
                    workout=workout_obj,
                    exercise_id=exercise['exercise'],
                    sets=exercise['sets'],
                    reps=exercise['reps'],
                )
                workout_exercise_objs.append(workout_exercise_obj)

        Workout.objects.bulk_create(workout_objs)
        WorkoutExercise.objects.bulk_create(workout_exercise_objs)
        ProgramWorkout.objects.bulk_create(program_workout_objs)


class AINutritionPlanView(APIView):
    def post(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)
