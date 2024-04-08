from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from django.urls import path
from . import views


urlpatterns = [
    path('api/token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
   # path('accounts/login/', views.login_view, name='login'),
    #path('accounts/logout/', views.LogoutView.as_view(), name='logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterView.as_view(), name='auth_register'),
    #Profile
    path('api/profile/', views.getProfile, name='profile'),
    path('api/profile/update/', views.updateProfile, name='update-profile'),
]