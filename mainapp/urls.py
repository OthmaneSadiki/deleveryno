from django.urls import path
from .views import ApproveStockView, AssignDriverView, MessageDetailView, MessageListCreateView
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
    path('orders/<int:pk>/assign/', AssignDriverView.as_view(), name='assign-driver'),
    
    # Stock endpoints
    path('stock/', StockListCreateView.as_view(), name='stock-list-create'),
    path('stock/<int:pk>/', StockDetailView.as_view(), name='stock-detail'),

    # Stock approval endpoint
    path('stock/<int:pk>/approve/', ApproveStockView.as_view(), name='approve-stock'),
    
    # Admin stock management endpoint (for listing all stocks)
    path('admin/stock/', StockListCreateView.as_view(), name='admin-stock-list'),

    # Message endpoints
    path('messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
   
    
    
]