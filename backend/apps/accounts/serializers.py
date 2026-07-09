# apps/accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Organization

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "organization",
            "role",
            "is_agent",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "organization",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that returns user data with tokens"""

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user data to response
        user = self.user
        data["user"] = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "organization": (
                {
                    "id": str(user.organization.id) if user.organization else None,
                    "name": user.organization.name if user.organization else None,
                    "slug": user.organization.slug if user.organization else None,
                }
                if user.organization
                else None
            ),
        }

        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, min_length=8)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError("New passwords do not match")
        return data


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


# Add these serializers


class UserProfileSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "organization",
            "role",
            "bio",
            "phone",
            "department",
            "avatar",
            "two_factor_enabled",
            "email_notifications",
            "browser_notifications",
            "timezone",
            "date_joined",
            "last_login",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "username",
            "role",
            "organization",
            "date_joined",
            "last_login",
            "two_factor_enabled",
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "bio",
            "phone",
            "department",
            "timezone",
            "email_notifications",
            "browser_notifications",
            "avatar",
        ]
        extra_kwargs = {
            "email": {"required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }


class AvatarUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["avatar"]


class TwoFactorSetupSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=6, max_length=6)


class TwoFactorVerifySerializer(serializers.Serializer):
    token = serializers.CharField(min_length=6, max_length=6)


class TwoFactorDisableSerializer(serializers.Serializer):
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data
