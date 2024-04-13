from datetime import datetime

import pytz
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from pytz import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Booking, Office, Room, Seat
from .serializers import OfficeSerializer, RoomSerializer, SeatSerializer, BookingSerializer, BookingHistorySerializer


class OfficeViewSet(viewsets.ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class SeatViewSet(viewsets.ModelViewSet):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    user = request.user
    data = request.data.copy()
    server_timezone = pytz.timezone(settings.TIME_ZONE)
    current_time = server_timezone.localize(datetime.now())
    data['user'] = user.pk
    data['start_time'] = server_timezone.localize(datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%SZ'))
    data['end_time'] = server_timezone.localize(datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%SZ'))

    with transaction.atomic():
        serializer = BookingSerializer(data=data)
        if serializer.is_valid():
            # Проверка доступности места для бронирования
            seat_id = data.get('seat')
            if seat_id:
                try:
                    seat = Seat.objects.select_for_update().get(id=seat_id)
                    existing_bookings_for_seat = Booking.objects.filter(seat=seat, is_active=True)
                    for booking in existing_bookings_for_seat:
                        if (data['start_time'] < booking.end_time and data['end_time'] > booking.start_time):
                            return Response({"error": "Seat is already booked for this time period."},
                                            status=status.HTTP_400_BAD_REQUEST)
                    # Если нет пересечений с другими бронированиями, обновляем статус места
                    seat.is_booked = True
                    seat.save()
                except Seat.DoesNotExist:
                    return Response({"error": "Seat does not exist."}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request):
    user = request.user
    booking_id = request.data.get('booking_id')  # Предполагается, что ID брони передается в теле запроса
    booking = get_object_or_404(Booking, id=booking_id, user=user)

    if request.method == 'POST':
        booking.cancel_booking()
        return Response({'message': 'Booking cancelled successfully.'})
    else:
        return Response({'error': 'Invalid request method.'}, status=405)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_bookings(request):
    user = request.user
    bookings = Booking.objects.filter(user=user, is_active=True)
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_history(request):
    user = request.user
    bookings = Booking.objects.filter(user=user)
    serializer = BookingHistorySerializer(bookings, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_seats(request):
    user = request.user
    query_params = request.query_params
    date = query_params.get('date')
    if not date:
        return Response({"error": "Date parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    server_timezone = pytz.timezone(settings.TIME_ZONE)
    selected_date = server_timezone.localize(selected_date)
    current_time = server_timezone.localize(datetime.now())
    print(selected_date)
    print(current_time)
    if selected_date < current_time:
        return Response({"error": "Selected date is in the past."}, status=status.HTTP_400_BAD_REQUEST)

    start_of_day = selected_date.replace(hour=0, minute=0, second=0)
    end_of_day = selected_date.replace(hour=23, minute=59, second=59)

    overlapping_bookings = Booking.objects.filter(
        Q(start_time__lte=end_of_day, end_time__gte=start_of_day) |
        Q(start_time__gte=start_of_day, end_time__lte=end_of_day)
    )

    all_seats = Seat.objects.all()

    available_seats = [seat for seat in all_seats if not overlapping_bookings.filter(seat=seat).exists()]

    serializer = SeatSerializer(available_seats, many=True)

    response_data = {
        "date": date,
        "available_seats": serializer.data,
    }

    return Response(response_data, status=status.HTTP_200_OK)
