from django.urls import path
from users import views

app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CookieTokenObtainPairView.as_view(), name='login'),
    path('refresh/', views.CookieTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', views.CookieLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]
