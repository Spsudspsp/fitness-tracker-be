from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from nutrition.models import FoodItem, Meal, MealItem

User = get_user_model()


class MealAPITests(APITestCase):
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

        self.predefined_oats = FoodItem.objects.create(
            user=None,
            name='Oats',
            calories=389,
            carbs=66,
            proteins=17,
            fats=7,
        )
        self.own_yogurt = FoodItem.objects.create(
            user=self.user,
            name='Greek yogurt',
            calories=59,
            carbs=4,
            proteins=10,
            fats=0,
        )
        self.other_banana = FoodItem.objects.create(
            user=self.other_user,
            name='Other banana',
            calories=89,
            carbs=23,
            proteins=1,
            fats=0,
        )

    def test_create_meal_allows_predefined_and_request_user_food_items(self):
        response = self.client.post(
            reverse('meal-list'),
            {
                'name': 'Breakfast bowl',
                'ingredients': [
                    {'food_item': str(self.predefined_oats.id), 'quantity': 80},
                    {'food_item': str(self.own_yogurt.id), 'quantity': 200},
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        meal = Meal.objects.get()
        self.assertEqual(meal.user, self.user)
        self.assertCountEqual(
            MealItem.objects.values_list('food_item_id', 'quantity'),
            [
                (self.predefined_oats.id, 80),
                (self.own_yogurt.id, 200),
            ],
        )

    def test_create_meal_rejects_other_user_food_item(self):
        response = self.client.post(
            reverse('meal-list'),
            {
                'name': 'Invalid meal',
                'ingredients': [
                    {'food_item': str(self.other_banana.id), 'quantity': 120},
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Meal.objects.count(), 0)
