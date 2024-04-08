from django.contrib import admin
from .models import Booking, Office, Room, Seat


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['name', 'location']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['office', 'name']


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['room', 'number', 'is_booked']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'seat', 'start_time', 'end_time', 'is_active', 'is_expired']
    list_filter = ['is_active']
    search_fields = ['user__username', 'seat__number']
