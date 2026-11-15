from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
)


@extend_schema(
    tags=['Auth'],
    summary='Register a new candidate or recruiter',
    description='Public endpoint for creating a candidate or recruiter account.',
    responses={
        201: UserDetailSerializer,
        400: OpenApiResponse(description='Validation error or duplicate email/username'),
    }
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output_serializer = UserDetailSerializer(user)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Auth'],
    summary='User login',
    description='Authenticates with username and password, returning JWT access and refresh tokens.',
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=['Auth'],
    summary='Refresh access token',
    description='Issues a new short-lived JWT access token given a valid long-lived refresh token.',
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema(
    tags=['Auth'],
    summary='Current authenticated user profile',
    description='Retrieves profile details for the currently logged in user.',
    responses={
        200: UserDetailSerializer,
        401: OpenApiResponse(description='Authentication required'),
    }
)
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
