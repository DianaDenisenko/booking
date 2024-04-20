from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()

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
            if hasattr(related_manager, 'all_with_deleted'):
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


class BookingManager(models.Manager):
    def update_expired_bookings(self):
        expired_bookings = self.filter(end_time__lt=timezone.now(), is_active=True)
        expired_bookings.update(is_active=False)


class Booking(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = BookingManager()

    def is_expired(self):
        return self.end_time < timezone.now()
