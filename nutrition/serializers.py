from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from rest_framework.fields import HiddenField

from nutrition import models
from nutrition.models import FoodItem


class FoodItemSerializer(serializers.ModelSerializer):
    user = HiddenField(default=serializers.CurrentUserDefault())
    is_predefined = serializers.BooleanField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='fooditem-detail', read_only=True)

    class Meta:
        model = models.FoodItem
        fields = '__all__'


class MealItemSerializer(serializers.ModelSerializer):
    food_item = serializers.PrimaryKeyRelatedField(queryset=FoodItem.objects.none(), write_only=True)

    class Meta:
        model = models.MealItem
        fields = ('food_item', 'quantity')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['food_item'].queryset = FoodItem.objects.filter(
                Q(user__isnull=True) | Q(user=request.user)
            )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        food_item = FoodItemSerializer(instance.food_item, context=self.context).data
        data['food_item'] = food_item
        return data

class MealSerializer(serializers.ModelSerializer):
    ingredients = MealItemSerializer(many=True, source='mealitem_set', allow_empty=False)
    user = HiddenField(default=serializers.CurrentUserDefault())
    url = serializers.HyperlinkedIdentityField(view_name='meal-detail', read_only=True)

    class Meta:
        model = models.Meal
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('mealitem_set')
        meal = models.Meal.objects.create(**validated_data)
        models.MealItem.objects.bulk_create(
            [models.MealItem(meal=meal, **entry) for entry in ingredients_data]
        )
        return meal

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('mealitem_set', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if ingredients_data is not None:
            instance.mealitem_set.all().delete()
            models.MealItem.objects.bulk_create(
                [models.MealItem(meal=instance, **entry) for entry in ingredients_data]
            )

        return instance
