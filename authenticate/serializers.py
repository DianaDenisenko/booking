from datetime import datetime
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )

    def validate_date_of_birth(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Invalid date of birth.")
        return value

    def validate_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError(
                "First name and last name should contain only letters."
            )
        return value

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "date_of_birth",
        )

    def validate(self, attrs):
        if "first_name" in attrs:
            attrs["first_name"] = self.validate_name(attrs["first_name"])

        if "last_name" in attrs:
            attrs["last_name"] = self.validate_name(attrs["last_name"])

        if "date_of_birth" in attrs:
            attrs["date_of_birth"] = self.validate_date_of_birth(attrs["date_of_birth"])
        return attrs

    def create(self, validated_data):
        user = CustomUser.objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            date_of_birth=validated_data.get("date_of_birth", None),
        )

        user.set_password(validated_data["password"])
        user.save()

        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        user = self.context["request"].user
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")

        if not user.check_password(old_password):
            raise serializers.ValidationError("Invalid old password")

        if old_password == new_password:
            raise serializers.ValidationError(
                "New password should be different from the old one."
            )

        validate_password(new_password)

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        user.set_password(validated_data["new_password"])
        user.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        exclude = ["password"]
