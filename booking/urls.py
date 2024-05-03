from django.urls import path, include
from rest_framework.routers import SimpleRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from .views import (
    OfficeViewSet,
    RoomViewSet,
    SeatViewSet,
    create_booking,
    list_my_bookings,
    booking_history,
    available_seats,
    cancel_booking,
)

router = SimpleRouter(trailing_slash=False)
router.register("offices", OfficeViewSet, basename="office")
router.register("rooms", RoomViewSet, basename="room")
router.register("seats", SeatViewSet, basename="seat")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/create-booking/", create_booking, name="create-booking"),
    path("api/cancel-booking/", cancel_booking, name="cancel-booking"),
    path("api/list-my-bookings/", list_my_bookings, name="list-my-bookings"),
    path("api/booking-history/", booking_history, name="booking-history"),
    path("api/available-seats/", available_seats, name="available-seats"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
