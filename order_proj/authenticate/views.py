from datetime import timedelta, datetime

from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import render
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
      #  jwt_authentication = JWTAuthentication()
     #   jwt_authentication.authenticate(request=None, user=user)
        # Add custom claims
        token['username'] = user.username
        # Get current time
        current_time = datetime.utcnow()

        # Check if access token has expired
        if token['exp'] < current_time.timestamp():
            # If token is expired, create a new refresh token
            refresh = RefreshToken.for_user(user)
            # Set a new expiration time for access token
           # token.set_exp(timedelta(minutes=5))  # Set expiration time (e.g., 5 minutes)
            # Return both access and refresh tokens
            return {
                'access': str(token),
                'refresh': str(refresh),
            }

        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2', 'bio')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = CustomUser.objects.create(
            username=validated_data['username'],
            bio=validated_data['bio']
        )

        user.set_password((validated_data['password']))
        user.save()

        return user

class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = '__all__'




#Login User
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

#Register User
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer




#api/profile  and api/profile/update
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getProfile(request):
    user = request.user
    serializer = ProfileSerializer(user, many=False)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateProfile(request):
    user = request.user
    serializer = ProfileSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


