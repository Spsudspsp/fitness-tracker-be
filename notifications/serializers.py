from rest_framework import serializers

from notifications import models


class NotificationSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='notification-detail', read_only=True)

    class Meta:
        model = models.Notification
        fields = ('id', 'type', 'title', 'content', 'created')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context['view'].action != 'list':
            data.pop('url')
        return data
