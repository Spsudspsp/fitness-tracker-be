from rest_framework import serializers


class PlanRequestSerializer(serializers.Serializer):
    provider = serializers.CharField()
    experience_level = serializers.CharField()
    goal_weight = serializers.DecimalField(max_digits=5, decimal_places=2)
    notes = serializers.CharField()
    days_per_week = serializers.IntegerField(min_value=1, max_value=7)
