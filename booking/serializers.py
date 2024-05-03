from datetime import datetime
import pytz
from rest_framework import serializers
from django.conf import settings
from .models import Office, Room, Seat, Booking

MIN_BOOKING_DURATION = settings.MIN_BOOKING_DURATION
MAX_BOOKING_DURATION = settings.MAX_BOOKING_DURATION


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = "__all__"


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = "__all__"


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        exclude = ["user"]

    def validate(self, data):
        server_timezone = pytz.timezone(settings.TIME_ZONE)
        user = self.context["request"].user
        data["user"] = user.pk
        data["start_time"] = data["start_time"]
        data["end_time"] = data["end_time"]

        current_time = server_timezone.localize(datetime.now())
        start_time = data["start_time"]
        end_time = data["end_time"]
        if start_time < current_time:
            raise serializers.ValidationError("Cannot book in the past.")
        if (end_time - start_time).total_seconds() > MAX_BOOKING_DURATION:
            raise serializers.ValidationError("Booking duration exceeds limit.")

        if (end_time - start_time).total_seconds() < MIN_BOOKING_DURATION:
            raise serializers.ValidationError("Can be booked for a minimum of 1 hour.")

        return data


class BookingHistorySerializer(serializers.Serializer):
    date = serializers.DateField()
    seat_id = serializers.IntegerField()

    def validate(self, data):
        try:
            datetime.strptime(str(data["date"]), "%Y-%m-%d").date()
        except ValueError:
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")

        return data


class AvailableSeatsSerializer(serializers.Serializer):
    date = serializers.DateField()
    room_id = serializers.IntegerField()
    page = serializers.IntegerField()

    def validate_date(self, value):
        server_timezone = pytz.timezone(settings.TIME_ZONE)
        current_time = server_timezone.localize(datetime.now())

        try:
            selected_date = datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")

        if selected_date < current_time.date():
            raise serializers.ValidationError("Booking for past dates is not allowed.")

        return value

    def validate_room_id(self, value):
        if not value:
            raise serializers.ValidationError("room_id parameter is required.")
        return value


class AvailableSeatsResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    pagination = serializers.DictField()

    @staticmethod
    def format_response_data(cls, date, paginated_list):
        paginated_available_times_by_seat = {}
        for seat_id, time in paginated_list:
            paginated_available_times_by_seat.setdefault(seat_id, []).append(time)

        return {"date": date, "pagination": paginated_available_times_by_seat}
