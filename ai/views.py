from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import ViewSet


class AIServiceViewSet(ViewSet):
    @action(methods=['post'], detail=False, url_path='generate-training-plan')
    def generate_training_plan(self, request, *args, **kwargs):
        return Response(status=HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='generate-nutrition-plan')
    def generate_nutrition_plan(self, request, *args, **kwargs):
        return Response(status=HTTP_200_OK)