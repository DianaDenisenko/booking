from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import viewsets, status, pagination
from rest_framework.response import Response

from .models import Booking, Office, Room, Seat
from .serializers import (
    OfficeSerializer,
    RoomSerializer,
    SeatSerializer,
    BookingSerializer,
    BookingHistorySerializer,
    AvailableSeatsSerializer,
    AvailableSeatsResponseSerializer,
)
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)


class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == "list" or self.action == "retrieve":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class OfficeViewSet(BaseViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer


class RoomViewSet(BaseViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class SeatViewSet(BaseViewSet):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer


@extend_schema(
    request=BookingSerializer,
    responses={
        201: BookingSerializer,
        400: {"type": "object", "properties": {"error": {"type": "string"}}},
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_booking(request):
    data = request.data.copy()
    user = request.user
    serializer = BookingSerializer(data=data, context={"request": request})
    if serializer.is_valid():
        seat = data.get("seat")
        if Booking.objects.has_conflicting_bookings(
            seat, data["start_time"], data["end_time"]
        ):
            return Response(
                {"error": "Seat is already booked for this time period."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=None,
    parameters=[
        OpenApiParameter(
            name="booking_id",
            type=int,
            location=OpenApiParameter.QUERY,
            description="ID of the booking to cancel",
        )
    ],
    responses={
        200: OpenApiResponse(description="Booking cancelled successfully."),
        404: OpenApiResponse(description="Booking not found."),
        405: OpenApiResponse(description="Invalid request method."),
    },
    methods=["POST"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_booking(request):
    user = request.user
    booking_id = request.data.get("booking_id")
    booking = get_object_or_404(Booking, id=booking_id, user=user)

    if request.method == "POST":
        booking.delete()
        return Response({"message": "Booking cancelled successfully."})
    else:
        return Response({"error": "Invalid request method."}, status=405)


@extend_schema(
    responses={200: BookingSerializer(many=True)},
    description="Get list of bookings for the authenticated user.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_my_bookings(request):
    user = request.user
    Booking.objects.update_expired_bookings()
    bookings = Booking.objects.filter(user=user, is_active=True)
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="seat_id",
            type=int,
            location=OpenApiParameter.QUERY,
            description="ID of the seat",
        ),
        OpenApiParameter(
            name="date",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Date in YYYY-MM-DD format",
        ),
    ],
    responses={
        200: BookingSerializer(many=True),
        400: OpenApiResponse(description="Bad request."),
    },
    description="Get booking history for the authenticated user.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def booking_history(request):
    user = request.user
    data = request.query_params
    Booking.objects.update_expired_bookings()
    serializer = BookingHistorySerializer(data=data)
    if serializer.is_valid():
        bookings = Booking.objects.booking_history(
            seat_id=data["seat_id"], date=data["date"], user=user
        )
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="room_id",
            type=int,
            location=OpenApiParameter.QUERY,
            description="ID of the room",
        ),
        OpenApiParameter(
            name="date",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Date in YYYY-MM-DD format",
        ),
    ],
    responses={
        200: AvailableSeatsResponseSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def available_seats(request):
    serializer = AvailableSeatsSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    date = serializer.validated_data["date"]
    room_id = serializer.validated_data["room_id"]

    available_times_by_seat = Seat.get_available_seats(date, room_id)
    response_data = {
        "date": date,
        "time_by_seat": available_times_by_seat,
    }
    return Response(response_data, status=status.HTTP_200_OK)
