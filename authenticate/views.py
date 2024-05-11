from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import CustomUser
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    ChangePasswordSerializer,
    ProfileSerializer,
    RegisterSerializer,
    MyTokenObtainPairSerializer,
)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# Register User
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


@extend_schema(
    request=ChangePasswordSerializer,
    description="Change password",
    responses={
        200: OpenApiResponse(
            description="Password updated successfully.",
        ),
        400: OpenApiResponse(
            description="Bad request.",
        ),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(
        data=request.data, context={"request": request}, instance=request.user
    )
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Password updated successfully."})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# api/profile  and api/profile/update
@extend_schema(
    responses={200: ProfileSerializer},
    description="Get profile details for the authenticated user.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request):
    user = request.user
    serializer = ProfileSerializer(user, many=False)
    return Response(serializer.data)


@extend_schema(
    request=ProfileSerializer,
    responses={200: ProfileSerializer},
    description="Update profile details for the authenticated user.",
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user

    if (
        "is_superuser" in request.data
        and request.data["is_superuser"]
        and not user.is_superuser
    ):
        return Response(
            {"error": "Regular users cannot assign themselves as superusers."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ProfileSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)
