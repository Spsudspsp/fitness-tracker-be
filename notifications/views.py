from rest_framework import viewsets

from notifications import models, serializers


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Notification.objects.all()
    serializer_class = serializers.NotificationSerializer

    def get_queryset(self):
        return self.queryset.for_user(user=self.request.user)
