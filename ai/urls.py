from django.urls import path

from ai import views

urlpatterns = [
    path('generate-training-plan', views.AITrainingPlanView.as_view(), name='training-plan'),
    path('generate-nutrition-plan', views.AINutritionPlanView.as_view(), name='nutrition-plan')
]
