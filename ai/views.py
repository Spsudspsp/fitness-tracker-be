from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from ai import serializers
from ai.tasks import generate_training_program

User = get_user_model()


class AITrainingProgramView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = serializers.PlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.data
        data['user_id'] = request.user.id
        generate_training_program.delay(data)

        return Response(status=status.HTTP_204_NO_CONTENT)

# TODO implement nutrition plan generation
class AINutritionPlanView(APIView):
    def post(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)
