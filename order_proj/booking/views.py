import os
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Booking, Office, Room, Seat
from .serializers import OfficeSerializer, RoomSerializer, SeatSerializer, BookingSerializer, BookingHistorySerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

load_dotenv()

BOOKING_DURATION = int(os.getenv('BOOKING_DURATION'))
END_OF_WORK_HOUR = int(os.getenv('END_OF_WORK_HOUR')) - 1
START_OF_WORK_HOUR = int(os.getenv('START_OF_WORK_HOUR'))
START_OF_WORK_MINUTE = int(os.getenv('START_OF_WORK_MINUTE'))
END_OF_WORK_MINUTE = int(os.getenv('END_OF_WORK_MINUTE'))


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
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
        400: {'type': 'object', 'properties': {'error': {'type': 'string'}}}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    """
    Create a booking.
    """
    user = request.user
    data = request.data.copy()
    server_timezone = pytz.timezone(settings.TIME_ZONE)
    data['user'] = user.pk
    data['start_time'] = server_timezone.localize(datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M'))
    data['end_time'] = server_timezone.localize(datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M'))

    with transaction.atomic():
        serializer = BookingSerializer(data=data)
        if serializer.is_valid():
            seat_id = data.get('seat')
            if seat_id:
                seat = get_object_or_404(Seat, id=seat_id)
                if has_conflicting_bookings(seat, data['start_time'], data['end_time']):
                    return Response({"error": "Seat is already booked for this time period."},
                                    status=status.HTTP_400_BAD_REQUEST)
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def has_conflicting_bookings(seat, start_time, end_time):
    existing_bookings = Booking.objects.filter(seat=seat, is_active=True)
    for booking in existing_bookings:
        if start_time < booking.end_time and end_time > booking.start_time:
            return True
    return False


@extend_schema(
    request=None,
    parameters=[
        OpenApiParameter(name='booking_id', type=int, location=OpenApiParameter.QUERY, description='ID of the booking to cancel')
    ],
    responses={200: {'message': 'Booking cancelled successfully.'}},
    methods=["POST"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request):
    user = request.user
    booking_id = request.data.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id, user=user)

    if request.method == 'POST':
        booking.delete()
        return Response({'message': 'Booking cancelled successfully.'})
    else:
        return Response({'error': 'Invalid request method.'}, status=405)

@extend_schema(
    responses={200: BookingSerializer(many=True)},
    description='Get list of bookings for the authenticated user.'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_bookings(request):
    user = request.user
    Booking.objects.update_expired_bookings()
    bookings = Booking.objects.filter(user=user, is_active=True)
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)

@extend_schema(
    responses={200: BookingHistorySerializer(many=True)},
    description='Get booking history for the authenticated user.'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_history(request):
    user = request.user
    Booking.objects.update_expired_bookings()
    bookings = Booking.objects.filter(user=user)
    serializer = BookingHistorySerializer(bookings, many=True)
    return Response(serializer.data)

@extend_schema(
    parameters=[
        OpenApiParameter(name='date', type=str, location=OpenApiParameter.QUERY, description='Date of the booking in format YYYY-MM-DD'),
        OpenApiParameter(name='room_id', type=int, location=OpenApiParameter.QUERY, description='ID of the room to check available seats'),
    ],
    description='Get available seats for a specific date and room.',
    responses={
        200: OpenApiResponse(
            description='Response when seats are available',
            examples=[
                OpenApiExample(
                    name='Available seats example',
                    summary='Example of available seats response',
                    description='Response when seats are available',
                    value={
                        "date": "2024-04-30",
                        "available_times_by_seat": {
                            "1": [("09:00", "10:00"), ("10:30", "11:30")],
                            "2": [("09:00", "10:00"), ("10:30", "11:30")],
                        }
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_seats(request):
    query_params = request.query_params
    date = query_params.get('date')
    room_id = query_params.get('room_id')
    server_timezone = pytz.timezone(settings.TIME_ZONE)
    current_time = server_timezone.localize(datetime.now())
    if not room_id:
        return Response({"error": "room_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not date:
        return Response({"error": "Date parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    start_of_day = server_timezone.localize(datetime.combine(selected_date, datetime.min.time()))
    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)
    if end_of_day < current_time:
        return Response({"error": "Booking for past dates is not allowed."}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve seats for the specified room with related bookings
    seats = Seat.objects.filter(room=room_id).prefetch_related(
        Prefetch('booking_set', queryset=Booking.objects.filter(
            Q(start_time__date=selected_date) |  # Include bookings that start on selected date
            Q(end_time__date=selected_date),     # Include bookings that end on selected date
            is_active=True)
        )
    )

    if not seats.exists():
        return Response({"error": "No seats found for the specified room."}, status=status.HTTP_404_NOT_FOUND)

    # Iterate over seats to find available times for each seat
    available_times_by_seat = {}
    for seat in seats.all():
        bookings_on_date = seat.booking_set.all()
        available_times = []
        interval_start = start_of_day.replace(hour=START_OF_WORK_HOUR, minute=START_OF_WORK_MINUTE)

        # Adjust interval start time if the selected date is the current date
        if selected_date == current_time.date():
            interval_start = max(interval_start,
                                 current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))

        while interval_start <= end_of_day.replace(hour=END_OF_WORK_HOUR, minute=END_OF_WORK_MINUTE):
            interval_end = interval_start + timedelta(hours=BOOKING_DURATION)
            # Check if the interval overlaps with any existing bookings
            overlapping_bookings = bookings_on_date.filter(
                Q(start_time__lt=interval_end, end_time__gt=interval_start) |
                Q(start_time__gte=interval_start, end_time__lte=interval_end)
            )
            if not overlapping_bookings.exists():
                available_times.append((interval_start.strftime('%H:%M'), interval_end.strftime('%H:%M')))
            interval_start += timedelta(hours=BOOKING_DURATION)

        available_times_by_seat[seat.id] = available_times

    response_data = {
        "date": date,
        "available_times_by_seat": available_times_by_seat,
    }

    return Response(response_data, status=status.HTTP_200_OK)

