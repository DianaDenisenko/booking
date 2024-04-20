from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from django.urls import path
from . import views
from .views import changePassword

urlpatterns = [
    path('api/token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', views.RegisterView.as_view(), name='auth_register'),
    # Profile
    path('api/profile/', views.getProfile, name='profile'),
    path('api/change-password/', changePassword, name='change-password'),
    path('api/profile/update/', views.updateProfile, name='update-profile'),
]