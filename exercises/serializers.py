from rest_framework import serializers

from exercises import models


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Exercise
        fields = '__all__'

