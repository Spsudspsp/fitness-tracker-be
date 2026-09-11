from rest_framework import serializers


class PlanRequestSerializer(serializers.Serializer):
    goal_weight = serializers.DecimalField(max_digits=5, decimal_places=2)
    notes = serializers.CharField()
