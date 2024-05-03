from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import path
from . import views

urlpatterns = [
    path("api/token/", views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/register/", views.RegisterView.as_view(), name="auth_register"),
    # Profile
    path("api/profile/", views.get_profile, name="profile"),
    path("api/change-password/", views.change_password, name="change-password"),
    path("api/profile/update/", views.update_profile, name="update-profile"),
]
