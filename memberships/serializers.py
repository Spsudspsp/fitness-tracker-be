from rest_framework import serializers

from memberships import models


class GymSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='gym-detail', lookup_field='pk')

    class Meta:
        model = models.Gym
        fields = '__all__'

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if self.context['view'].action != 'list':
            data.pop('url')
        return data


class MembershipSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    duration_months = serializers.IntegerField(min_value=1, write_only=True, required=False)

    class Meta:
        model = models.Membership
        fields = '__all__'
        read_only_fields = ('expiration_date', 'notify_at', 'status')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if (self.instance is None or not self.instance.is_active) and 'duration_months' not in attrs:
            raise serializers.ValidationError({'duration_months': 'This field is required.'})

        if not self.instance and 'start_date' not in attrs:
            raise serializers.ValidationError({'start_date': 'This field is required.'})

        return attrs

    def create(self, validated_data):
        duration_months = validated_data.pop('duration_months')
        membership = models.Membership(**validated_data)
        membership.set_dates(start_date=validated_data['start_date'], duration_months=duration_months)
        membership.save()
        return membership

    def update(self, instance, validated_data):
        duration_months = validated_data.pop('duration_months', None)
        membership = super().update(instance, validated_data)
        if duration_months is not None:
            membership.set_dates(duration_months=duration_months)
            membership.save()
        return membership

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['gym'] = GymSerializer(instance.gym, context=self.context).data
        return data


class RenewMembershipSerializer(serializers.Serializer):
    duration_months = serializers.IntegerField(min_value=1)


class CancelMembershipSerializer(serializers.Serializer):
    pass
