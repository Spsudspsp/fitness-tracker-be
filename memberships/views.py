from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from memberships import models, serializers

class GymViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Gym.objects.all()
    serializer_class = serializers.GymSerializer

class MembershipViewSet(viewsets.ModelViewSet):
    queryset = models.Membership.objects.all()
    serializer_class = serializers.MembershipSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).select_related('gym')

    @action(detail=True, methods=['post'])
    def cancel(self, request, *args, **kwargs):
        membership = self.get_object()
        membership.set_status_canceled()
        membership.save()
        return Response(self.serializer_class(membership, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['post'])
    def renew(self, request, *args, **kwargs):
        membership = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership.set_dates(duration_months=serializer.validated_data['duration_months'])
        return Response(self.serializer_class(membership, context=self.get_serializer_context()).data)

    def get_serializer_class(self):
        return self.action_serializers_mapping.get(self.action) or self.serializer_class

    action_serializers_mapping = dict(
        renew=serializers.RenewMembershipSerializer,
        cancel=serializers.CancelMembershipSerializer,
    )