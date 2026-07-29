from django.contrib.postgres.fields import ArrayField
from django.db import models

from utils.models import UUIDModel


class MuscleGroup(models.TextChoices):
    CHEST = "chest", "Chest"
    BACK = "back", "Back"
    SHOULDERS = "shoulders", "Shoulders"
    BICEPS = "biceps", "Biceps"
    TRICEPS = "triceps", "Triceps"
    FOREARMS = "forearms", "Forearms"
    QUADRICEPS = "quadriceps", "Quadriceps"
    HAMSTRINGS = "hamstrings", "Hamstrings"
    GLUTES = "glutes", "Glutes"
    CALVES = "calves", "Calves"
    CORE = "core", "Core"
    FULL_BODY = "full_body", "Full body"


class Equipment(models.TextChoices):
    NONE = "none", "No equipment"
    BARBELL = "barbell", "Barbell"
    DUMBBELL = "dumbbell", "Dumbbell"
    EZ_BAR = "ez_bar", "EZ bar"
    TRAP_BAR = "trap_bar", "Trap bar"
    KETTLEBELL = "kettlebell", "Kettlebell"
    CABLE = "cable", "Cable"
    MACHINE = "machine", "Machine"
    SMITH_MACHINE = "smith_machine", "Smith machine"
    RESISTANCE_BAND = "resistance_band", "Resistance band"
    BENCH = "bench", "Bench"
    SQUAT_RACK = "squat_rack", "Squat rack"
    PULL_UP_BAR = "pull_up_bar", "Pull-up bar"
    DIP_BARS = "dip_bars", "Dip bars"
    SUSPENSION_TRAINER = "suspension_trainer", "Suspension trainer"
    MEDICINE_BALL = "medicine_ball", "Medicine ball"
    EXERCISE_BALL = "exercise_ball", "Exercise ball"
    FOAM_ROLLER = "foam_roller", "Foam roller"
    CARDIO_MACHINE = "cardio_machine", "Cardio machine"
    OTHER = "other", "Other"


class Exercise(UUIDModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    muscle_groups = ArrayField(models.CharField(max_length=255, choices=MuscleGroup.choices))
    equipment = ArrayField(models.CharField(max_length=255, choices=Equipment.choices))
