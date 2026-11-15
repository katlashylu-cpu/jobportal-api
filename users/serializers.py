from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role', 'date_joined')
        read_only_fields = ('id', 'date_joined')

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_role(self, value):
        if value not in [User.ROLE_CANDIDATE, User.ROLE_RECRUITER]:
            raise serializers.ValidationError(
                "Role must be either 'candidate' or 'recruiter'. Admin accounts cannot be self-registered."
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', User.ROLE_CANDIDATE),
        )


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'date_joined')
        read_only_fields = fields


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
        }
        return data
