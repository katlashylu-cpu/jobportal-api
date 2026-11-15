from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Health check endpoint returning system status.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Health'],
        summary='System health check',
        description='Returns the current health status of the API service.',
        responses={
            200: inline_serializer(
                name='HealthCheckResponse',
                fields={
                    'status': serializers.CharField(),
                    'service': serializers.CharField(),
                }
            )
        }
    )
    def get(self, request):
        return Response(
            {
                'status': 'healthy',
                'service': 'jobportal-api',
            },
            status=status.HTTP_200_OK
        )
