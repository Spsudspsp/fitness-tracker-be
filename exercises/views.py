from rest_framework.viewsets import ReadOnlyModelViewSet
from exercises import models
from exercises import serializers


class ExerciseListRetrieveView(ReadOnlyModelViewSet):
    queryset = models.Exercise.objects.all()
    serializer_class = serializers.ExerciseSerializer