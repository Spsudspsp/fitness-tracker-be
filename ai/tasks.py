import requests
from celery import shared_task
from decouple import config
from django.contrib.auth import get_user_model
from django.db import transaction

from ai.signals import training_program_generated
from exercises.models import Exercise
from exercises.serializers import ExerciseSerializer
from workouts.models import WorkoutExercise, ProgramWorkout, Workout, Program

TRAINING_PROGRAM_GENERATION_URL = f'{config('AI_SERVICE_URL')}/training_plans/generate'

User = get_user_model()

@shared_task
def generate_training_program(data):
    provider = data['ai_provider']

    user_id = data['user_id']
    user = User.objects.select_related('profile').get(pk=user_id)
    user_weight = float(user.profile.weight)
    goal_weight = float(data['goal_weight'])
    user_height = float(user.profile.height)
    user_age = user.profile.get_age()
    notes = data['notes']
    days_per_week = data['days_per_week']
    available_exercises = ExerciseSerializer(Exercise.objects.all(), many=True).data

    req = dict(
        provider='gemini',
        age=user_age,
        weight_kg=user_weight,
        height_cm=user_height,
        goal_weight=goal_weight,
        notes=notes,
        # TODO implement experience levels
        experience_level='beginner',
        days_per_week=days_per_week,
        available_exercises=available_exercises,
    )

    res = requests.post(
        TRAINING_PROGRAM_GENERATION_URL,
        json=req,
        headers={'Content-Type': 'application/json', 'x-service-key': config('AI_SERVICE_KEY')},
        timeout=120
    )
    res.raise_for_status()

    ai_data = res.json()
    program = create_training_program(user, ai_data)

    training_program_generated.send(
        sender=Program,
        user=user,
        program=program,
    )

@transaction.atomic
def create_training_program(user, data):
    program_name = data['name']
    program_description = data['description']

    program = Program.objects.create(
        user=user,
        name=program_name,
        description=program_description,
    )

    workouts = data['workouts']
    workout_objs = []
    program_workout_objs = []
    workout_exercise_objs = []

    for workout in workouts:
        workout_name = workout['name']
        workout_obj = Workout(
            user=user,
            name=workout_name,
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

    return program