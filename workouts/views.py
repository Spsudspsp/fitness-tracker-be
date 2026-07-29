from rest_framework import viewsets, permissions
from rest_framework.response import Response

from workouts import serializers, models


class WorkoutViewSet(viewsets.ModelViewSet):
    queryset = models.Workout.objects.all()
    serializer_class = serializers.WorkoutSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).prefetch_related('workoutexercise_set__exercise')

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = models.Program.objects.all()
    serializer_class = serializers.ProgramSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).prefetch_related('programworkout_set__workout__workoutexercise_set__exercise')