from django.urls import path
from .views import AssignDriverView, UserListView
from .views import (
    OrderListCreateView, OrderDetailView, OrderStatusUpdateView, 
    DriverOrderListView, SellerOrderListView,
    StockListCreateView, StockDetailView
)

urlpatterns = [
    # Order endpoints
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('driver/orders/', DriverOrderListView.as_view(), name='driver-orders'),
    path('seller/orders/', SellerOrderListView.as_view(), name='seller-orders'),
    
    # Stock endpoints
    path('stock/', StockListCreateView.as_view(), name='stock-list-create'),
    path('stock/<int:pk>/', StockDetailView.as_view(), name='stock-detail'),
    #user
    path('users/', UserListView.as_view(), name='user-list'),
    path('orders/<int:pk>/assign/', AssignDriverView.as_view(), name='assign-driver'),
]