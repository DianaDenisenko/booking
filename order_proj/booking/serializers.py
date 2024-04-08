from datetime import datetime

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


from rest_framework import serializers

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

    def validate(self, data):
        server_timezone = timezone('UTC')

        # Ограничение на бронирование в прошлом
        current_time = server_timezone.localize(datetime.now())
        start_time = data['start_time']
        end_time = data['end_time']
        # Проверка на бронирование в прошлом
        if start_time < current_time:
            raise serializers.ValidationError("Cannot book in the past.")

        # Проверка на длительность бронирования
        if (end_time - start_time).total_seconds() > 7 * 24 * 3600:  # 7 дней в секундах
            raise serializers.ValidationError("Booking duration exceeds limit.")

        # Проверка на минимальную длительность бронирования
        if (end_time - start_time).total_seconds() < 30 * 60:  # 30 минут в секундах
            raise serializers.ValidationError("Can be booked for a minimum of 30 minutes.")

        return data



class BookingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
