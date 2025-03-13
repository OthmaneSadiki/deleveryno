from django.urls import path
from .views import DebugView, SellerRegistrationView, DriverRegistrationView, LoginView, UserDetailView, UserListView, UserProfileView, ApproveUserView

urlpatterns = [
    path('register/seller/', SellerRegistrationView.as_view(), name='register-seller'),
    path('register/driver/', DriverRegistrationView.as_view(), name='register-driver'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/<int:pk>/approve/', ApproveUserView.as_view(), name='approve-user'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('debug/', DebugView.as_view(), name='debug'),
    path('users//', UserDetailView.as_view(), name='user-detail'),
    
]