from django.db import transaction
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from exercises.models import Exercise
from exercises.serializers import ExerciseSerializer
from workouts import models
from workouts.models import Workout, WorkoutExercise, Program


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all(), write_only=True)

    class Meta:
        model = models.WorkoutExercise
        fields = ('exercise', 'sets', 'reps')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        exercise = ExerciseSerializer(instance.exercise, context=self.context).data
        data['exercise'] = exercise
        return data



class WorkoutSerializer(serializers.ModelSerializer):
    exercises = WorkoutExerciseSerializer(many=True, allow_empty=False, source='workoutexercise_set')
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    url = serializers.HyperlinkedIdentityField(view_name='workout-detail', read_only=True)

    class Meta:
        model = models.Workout
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        exercise_data = validated_data.pop('workoutexercise_set')
        workout = Workout.objects.create(**validated_data)
        models.WorkoutExercise.objects.bulk_create(
            [models.WorkoutExercise(workout=workout, **entry) for entry in exercise_data]
        )
        return workout

    @transaction.atomic
    def update(self, instance, validated_data):
        exercise_data = validated_data.pop('workoutexercise_set', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if exercise_data is not None:
            instance.workoutexercise_set.all().delete()
            models.WorkoutExercise.objects.bulk_create(
                [models.WorkoutExercise(workout=instance, **entry) for entry in exercise_data]
            )
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        estimated_working_duration = 0
        estimated_resting_duration = 0
        for exercise in data['exercises']:
            estimated_resting_duration += 2 * (exercise['sets'] - 1)
            estimated_working_duration += 2 * exercise['sets']

        estimated_total_duration = estimated_working_duration + estimated_resting_duration
        data['estimated_working_duration'] = estimated_working_duration
        data['estimated_resting_duration'] = estimated_resting_duration
        data['estimated_total_duration'] = estimated_total_duration
        return data


class ProgramWorkoutSerializer(serializers.ModelSerializer):
    workout = PrimaryKeyRelatedField(queryset=Workout.objects.all(), write_only=True)

    class Meta:
        model = models.ProgramWorkout
        fields = ('workout', 'day')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        workout = WorkoutSerializer(instance.workout, context=self.context).data
        data['workout'] = workout
        return data


class ProgramSerializer(serializers.ModelSerializer):
    workouts = ProgramWorkoutSerializer(many=True, source='programworkout_set', allow_empty=False)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    url = serializers.HyperlinkedIdentityField(view_name='program-detail', read_only=True)

    class Meta:
        model = models.Program
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        workouts_data = validated_data.pop('programworkout_set')
        program = Program.objects.create(**validated_data)
        models.ProgramWorkout.objects.bulk_create(
            [models.ProgramWorkout(program=program, **entry) for entry in workouts_data]
        )
        return program

    @transaction.atomic
    def update(self, instance, validated_data):
        workouts_data = validated_data.pop('programworkout_set', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if workouts_data is not None:
            instance.programworkout_set.all().delete()
            models.ProgramWorkout.objects.bulk_create(
                [models.ProgramWorkout(program=instance, **entry) for entry in workouts_data]
            )

        return instance
