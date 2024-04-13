from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class Office(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)


class Room(models.Model):
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)


class Seat(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    number = models.IntegerField()
    is_booked = models.BooleanField(default=False)


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        return self.end_time < timezone.now()

    def cancel_booking(self):
        self.is_active = False
        self.save()
