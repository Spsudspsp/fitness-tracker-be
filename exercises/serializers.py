from rest_framework import serializers

from exercises import models


class ExerciseSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='exercise-detail', read_only=True)

    class Meta:
        model = models.Exercise
        fields = '__all__'

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if self.context['view'].action == 'retrieve':
            data.pop('url')
        return data
