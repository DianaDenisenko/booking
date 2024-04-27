from datetime import datetime
import os
from dotenv import load_dotenv
import pytz
from django.conf import settings
from pytz import timezone
from rest_framework import serializers

from .models import Office, Room, Seat, Booking


load_dotenv()

MIN_BOOKING_DURATION = float(os.getenv('MIN_BOOKING_DURATION'))
MAX_BOOKING_DURATION = float(os.getenv('MAX_BOOKING_DURATION'))


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

    def validate(self, data):
        server_timezone = pytz.timezone(settings.TIME_ZONE)

        current_time = server_timezone.localize(datetime.now())
        start_time = data['start_time']
        end_time = data['end_time']
        print(start_time)
        print(current_time)
        if start_time < current_time:
            raise serializers.ValidationError("Cannot book in the past.")
        print(MAX_BOOKING_DURATION)
        if (end_time - start_time).total_seconds() > MAX_BOOKING_DURATION:
            raise serializers.ValidationError("Booking duration exceeds limit.")

        if (end_time - start_time).total_seconds() < MIN_BOOKING_DURATION:
            raise serializers.ValidationError("Can be booked for a minimum of 1 hour.")

        return data


class BookingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
