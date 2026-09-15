from django.conf import settings
from django.contrib.auth import get_user_model, logout
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from users import serializers

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = serializers.RegisterSerializer
    permission_classes = (AllowAny,)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)

        access = res.data['access']
        refresh = res.data['refresh']

        res.set_cookie(
            'access_token',
            access,
            httponly=True,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )

        res.set_cookie(
            'refresh_token',
            refresh,
            httponly=True,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )

        res.data = {'detail': 'Login successful'}
        return res


class CookieTokenRefreshView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get('refresh_token')

        serializer = TokenRefreshSerializer(data=dict(refresh=refresh))
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data['access']

        res = Response(dict(detail='Token refreshed'))

        res.set_cookie(
            key='access_token',
            value=access,
            httponly=True,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )

        return res


class CookieLogoutView(APIView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        logout(request)

        res = Response(dict(detail='Logout successful'))

        res.delete_cookie('access_token')
        res.delete_cookie('refresh_token')

        return res