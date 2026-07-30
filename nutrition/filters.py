import django_filters

from nutrition import models


class FoodItemFilterSet(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    min_calories = django_filters.NumberFilter(field_name='calories', lookup_expr='gte')
    max_calories = django_filters.NumberFilter(field_name='calories', lookup_expr='lte')
    min_proteins = django_filters.NumberFilter(field_name='proteins', lookup_expr='gte')
    max_proteins = django_filters.NumberFilter(field_name='proteins', lookup_expr='lte')
    min_carbs = django_filters.NumberFilter(field_name='carbs', lookup_expr='gte')
    max_carbs = django_filters.NumberFilter(field_name='carbs', lookup_expr='lte')
    min_fats = django_filters.NumberFilter(field_name='fats', lookup_expr='gte')
    max_fats = django_filters.NumberFilter(field_name='fats', lookup_expr='lte')

    class Meta:
        model = models.FoodItem
        fields = []
