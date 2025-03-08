from django.urls import path
from .views import (
    AddressListCreateView, AddressDetailView,
    OrderListCreateView, OrderDetailView, OrderStatusUpdateView, 
    DriverOrderListView, SellerOrderListView,
    StockListCreateView, StockDetailView
)

urlpatterns = [
    # Address endpoints
    path('addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    
    # Order endpoints
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('driver/orders/', DriverOrderListView.as_view(), name='driver-orders'),
    path('seller/orders/', SellerOrderListView.as_view(), name='seller-orders'),
    
    # Stock endpoints
    path('stock/', StockListCreateView.as_view(), name='stock-list-create'),
    path('stock/<int:pk>/', StockDetailView.as_view(), name='stock-detail'),
]