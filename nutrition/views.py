from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated

from nutrition import models, serializers


class IsOwnerForWrites(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.id


class FoodItemViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.FoodItemSerializer
    permission_classes = [IsAuthenticated, IsOwnerForWrites]

    def get_queryset(self):
        return models.FoodItem.objects.filter(
            Q(user__isnull=True) | Q(user=self.request.user)
        )

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError(
                {'detail': 'This food item is used in a meal and cannot be deleted.'}
            ) from exc


class MealViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.MealSerializer
    permission_classes = [IsAuthenticated]
    queryset = models.Meal.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).prefetch_related(
            'mealitem_set__food_item'
        )
