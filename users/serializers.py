from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from users import models

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password_confirmation')
        read_only_fields = ('id',)

    def validate(self, data):
        pw1 = data['password']
        pw2 = data.pop('password_confirmation')

        if pw1 != pw2:
            raise serializers.ValidationError('Passwords must match.')

        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(request=self.context.get('request'), username=data['email'], password=data['password'])

        if not user:
            raise serializers.ValidationError('Invalid credentials')

        self.validated_data['user'] = user

        return data


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Profile
        fields = ('display_name', 'sex', 'birth_date', 'height', 'weight')
        read_only_fields = ('id',)


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'profile',
        )
        read_only_fields = ('id',)

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')

        instance = super().update(instance, validated_data)
        print(profile_data)
        if profile_data:
            profile_serializer = ProfileSerializer(instance=instance.profile, data=profile_data, partial=self.partial)
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        return instance
