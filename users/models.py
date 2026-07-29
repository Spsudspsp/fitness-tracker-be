from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.models import UUIDModel


class Sex(models.TextChoices):
    MALE = "M", "Male"
    FEMALE = "F", "Female"


class User(UUIDModel, AbstractUser):
    email = models.EmailField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    display_name = models.CharField(max_length=255, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    sex = models.CharField(
        max_length=1,
        choices=Sex.choices,
        null=True,
        blank=True,
    )
    height = models.DecimalField( # cm
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    weight = models.DecimalField( # kg
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
