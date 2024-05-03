from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from .models import Office, Room, Seat, Booking
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model

User = get_user_model()


class BookingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.token = AccessToken.for_user(self.user)

    def test_create_booking(self):
        office = Office.objects.create(name="Test Office", location="Test Location")
        room = Room.objects.create(office=office, name="Test Room")
        seat = Seat.objects.create(room=room, number=1)

        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)

        data = {
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "seat": seat.pk,
        }

        url = reverse("create-booking")
        response = self.client.post(
            url, data, format="json", HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)

    def test_list_my_bookings(self):
        office = Office.objects.create(name="Test Office", location="Test Location")
        room = Room.objects.create(office=office, name="Test Room")
        seat = Seat.objects.create(room=room, number=1)
        Booking.objects.create(
            user=self.user,
            seat=seat,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
        )

        url = reverse("list-my-bookings")
        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.token}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_booking_history(self):
        office = Office.objects.create(name="Test Office", location="Test Location")
        room = Room.objects.create(office=office, name="Test Room")
        seat = Seat.objects.create(room=room, number=1)
        Booking.objects.create(
            user=self.user,
            seat=seat,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
        )

        url = reverse("booking-history")
        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.token}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
