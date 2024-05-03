from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.utils import timezone


User = get_user_model()

BOOKING_DURATION = settings.BOOKING_DURATION
END_OF_WORK_HOUR = settings.END_OF_WORK_HOUR
START_OF_WORK_HOUR = settings.START_OF_WORK_HOUR
START_OF_WORK_MINUTE = settings.START_OF_WORK_MINUTE
END_OF_WORK_MINUTE = settings.END_OF_WORK_MINUTE


class SoftDeleteModel(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_active = False
        self._delete_related()
        self.save()

    def _delete_related(self):
        for related_object in self._meta.related_objects:
            related_name = related_object.get_accessor_name()
            related_manager = getattr(self, related_name)
            if hasattr(related_manager, "all_with_deleted"):
                for related_instance in related_manager.all_with_deleted():
                    related_instance.delete()
            else:
                for related_instance in related_manager.all():
                    related_instance.delete()


class Office(SoftDeleteModel):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)


class Room(SoftDeleteModel):
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)


class Seat(SoftDeleteModel):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    number = models.IntegerField()

    def get_available_times(self, date):
        timezone.activate(timezone.get_current_timezone())

        start_of_day = datetime.combine(date, datetime.min.time())
        start_of_day = timezone.make_aware(start_of_day)
        interval_start = max(
            start_of_day.replace(hour=START_OF_WORK_HOUR),
            timezone.localtime(timezone.now()).replace(
                minute=0, second=0, microsecond=0
            )
            + timedelta(hours=1),
        )
        end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)

        bookings = Booking.objects.filter(is_active=True)

        available_times = []

        while interval_start <= end_of_day.replace(hour=END_OF_WORK_HOUR, minute=0):
            interval_end = interval_start + timedelta(hours=BOOKING_DURATION)

            has_conflict = False
            for booking in bookings:
                if (
                    interval_start < booking.end_time
                    and interval_end > booking.start_time
                ):
                    has_conflict = True
                    break

            if not has_conflict:
                available_times.append(
                    (interval_start.strftime("%H:%M"), interval_end.strftime("%H:%M"))
                )

            interval_start += timedelta(hours=BOOKING_DURATION)

        return available_times


class BookingManager(models.Manager):
    def update_expired_bookings(self):
        expired_bookings = self.filter(end_time__lt=timezone.now(), is_active=True)
        expired_bookings.update(is_active=False)

    def has_conflicting_bookings(self, seat, start_time, end_time):
        overlaps_query = Q(start_time__lt=end_time, end_time__gt=start_time)
        conflicting_bookings = self.filter(seat=seat, is_active=True).filter(
            overlaps_query
        )
        return conflicting_bookings.exists()

    def booking_history(self, seat_id, date, user):
        overlaps_query = Q(start_time__date__lte=date, end_time__date__gte=date)
        history_bookings = self.filter(seat_id=seat_id, user=user).filter(
            overlaps_query
        )
        return history_bookings


class Booking(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = BookingManager()

    def is_expired(self):
        return self.end_time < timezone.now()

    def is_active_and_not_expired(self):
        return self.is_active and not self.is_expired()
