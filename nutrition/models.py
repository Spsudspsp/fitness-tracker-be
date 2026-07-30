from django.contrib.auth import get_user_model
from django.db import models

from utils.models import UUIDModel

User = get_user_model()


class FoodItem(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50)
    calories = models.PositiveIntegerField()
    carbs = models.PositiveIntegerField()
    proteins = models.PositiveIntegerField()
    fats = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    @property
    def is_predefined(self):
        return self.user_id is None


class Meal(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    ingredients = models.ManyToManyField(FoodItem, through='MealItem', related_name='meals')


class MealItem(models.Model):
    food_item = models.ForeignKey(FoodItem, on_delete=models.PROTECT)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
