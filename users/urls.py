from django.urls import path
from .views import SellerRegistrationView, DriverRegistrationView, LoginView, UserProfileView, ApproveUserView

urlpatterns = [
    path('register/seller/', SellerRegistrationView.as_view(), name='register-seller'),
    path('register/driver/', DriverRegistrationView.as_view(), name='register-driver'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/<int:pk>/approve/', ApproveUserView.as_view(), name='approve-user'),
]