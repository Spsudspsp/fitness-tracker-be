from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers

from exercises import views as exercises_views
from memberships import views as memberships_views
from notifications import views as notifications_views
from nutrition import views as nutrition_views
from workouts import views as workouts_views
from ai import views as ai_views

router = routers.DefaultRouter()

router.register('workouts', workouts_views.WorkoutViewSet, basename='workout')
router.register('programs', workouts_views.ProgramViewSet, basename='program')

router.register('exercises', exercises_views.ExerciseListRetrieveView)

router.register('gyms', memberships_views.GymViewSet, basename='gym')
router.register('memberships', memberships_views.MembershipViewSet, basename='membership')
router.register('food-items', nutrition_views.FoodItemViewSet, basename='fooditem')
router.register('meals', nutrition_views.MealViewSet, basename='meal')

router.register('notifications', notifications_views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path(
        'api-auth/',
        include('rest_framework.urls', namespace='rest_framework'),
    ),
    path('ai/', include('ai.urls')),
] + router.urls
