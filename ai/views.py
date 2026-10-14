from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from ai import serializers
from ai.models import consume_ai_usage
from ai.tasks import generate_training_program
from ai.throttles import AIGenerationThrottle

User = get_user_model()


class AITrainingProgramView(APIView):
    throttle_classes = [AIGenerationThrottle]

    def post(self, request, *args, **kwargs):
        serializer = serializers.PlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = request.user.id

        data = serializer.data
        data['user_id'] = user_id

        with transaction.atomic():
            consume_ai_usage(user_id=user_id)
            transaction.on_commit(
                lambda: generate_training_program.delay(data)
            )

        return Response(status=status.HTTP_202_ACCEPTED)


# TODO implement nutrition plan generation
class AINutritionPlanView(APIView):
    def post(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)
