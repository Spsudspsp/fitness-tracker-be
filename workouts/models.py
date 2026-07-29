from django.contrib.auth import get_user, get_user_model
from django.db import models

from exercises.models import Exercise
from utils.models import UUIDModel

User = get_user_model()

class Workout(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercises = models.ManyToManyField(Exercise, through='WorkoutExercise', related_name='workouts')

class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    sets = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()

class Program(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workouts = models.ManyToManyField(Workout, through='ProgramWorkout', related_name='programs')


class Day(models.TextChoices):
    MON = 'MON'
    TUE = 'TUE'
    WED = 'WED'
    THU = 'THU'
    FRI = 'FRI'
    SAT = 'SAT'
    SUN = 'SUN'


class ProgramWorkout(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    workout = models.ForeignKey(Workout, on_delete=models.SET_NULL, null=True)
    day = models.CharField(max_length=3, choices=Day.choices)

