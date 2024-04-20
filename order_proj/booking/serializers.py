from datetime import datetime

import pytz
from django.conf import settings
from pytz import timezone
from rest_framework import serializers

from .models import Office, Room, Seat, Booking


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

        if (end_time - start_time).total_seconds() > 7 * 24 * 3600:  # 7 days
            raise serializers.ValidationError("Booking duration exceeds limit.")

        if (end_time - start_time).total_seconds() < 60 * 60:  # 60 minutes
<<<<<<< HEAD
            raise serializers.ValidationError("Can be booked for a minimum of 30 minutes.")
=======
            raise serializers.ValidationError("Can be booked for a minimum of 1 hour.")
>>>>>>> a23593b (Address all identified issues)

        return data



class BookingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
