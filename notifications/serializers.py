from rest_framework import serializers

from notifications import models


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = ('id', 'type', 'title', 'content', 'created')
