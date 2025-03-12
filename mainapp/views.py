from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from users.serializers import UserSerializer

from .models import  Order, Stock
from .serializers import (
    OrderCreateSerializer, OrderDetailSerializer,
    OrderStatusUpdateSerializer, StockSerializer
)
from .permissions import (
    IsAdmin, IsSeller, IsDriver,
    IsAdminOrSellerOwner, IsAdminOrAssignedDriver
)

from django.contrib.auth import get_user_model
User = get_user_model()







class OrderListCreateView(generics.ListCreateAPIView):
    """
    API endpoint that allows orders to be viewed or created.
    GET: Admins can see all orders. Sellers can only see their own orders.
    POST: Only sellers can create orders.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        elif user.role == 'seller':
            return Order.objects.filter(seller=user)
        elif user.role == 'driver':
            return Order.objects.filter(driver=user)
        return Order.objects.none()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'created_at']


class SellerOrderListView(generics.ListAPIView):
    """
    API endpoint that allows a seller to view their own orders.
    """
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsSeller]
    
    def get_queryset(self):
        return Order.objects.filter(seller=self.request.user)


class DriverOrderListView(generics.ListAPIView):
    """
    API endpoint that allows a driver to view orders assigned to them.
    """
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsDriver]
    
    def get_queryset(self):
        return Order.objects.filter(driver=self.request.user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that allows a single order to be viewed, updated, or deleted.
    """
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSellerOwner]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        elif user.role == 'seller':
            return Order.objects.filter(seller=user)
        elif user.role == 'driver':
            return Order.objects.filter(driver=user)
        return Order.objects.none()


class OrderStatusUpdateView(APIView):
    """
    API endpoint that allows updating the status of an order.
    """
    permission_classes = [IsAuthenticated, IsAdminOrAssignedDriver]
    
    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        
        # Check permission for this object
        if not self.permission_classes[1]().has_object_permission(request, self, order):
            return Response(
                {"error": "You don't have permission to update this order's status."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Save the order first
            updated_order = serializer.save()
            
            # If status changed to delivered, update stock in a separate service call
            if updated_order.status == 'delivered':
                self._update_stock_on_delivery(updated_order)
                
            return Response(OrderDetailSerializer(updated_order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _update_stock_on_delivery(self, order):
        """Helper method to update stock when an order is delivered"""
        try:
            stock = Stock.objects.get(seller=order.seller, item_name=order.item)
            if stock.quantity >= order.quantity:
                stock.quantity -= order.quantity
                stock.save()
        except Stock.DoesNotExist:
            # Log this situation but don't break the flow
            print(f"Warning: Stock not found for item {order.item} from seller {order.seller.id}")


class StockListCreateView(generics.ListCreateAPIView):
    """
    API endpoint that allows stock items to be viewed or created.
    GET: Admins can see all stock items. Sellers can only see their own stock.
    POST: Only sellers can create stock items.
    """
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Stock.objects.all()
        elif user.role == 'seller':
            return Stock.objects.filter(seller=user)
        return Stock.objects.none()


class StockDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that allows a single stock item to be viewed, updated, or deleted.
    """
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSellerOwner]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Stock.objects.all()
        elif user.role == 'seller':
            return Stock.objects.filter(seller=user)
        return Stock.objects.none()

class AssignDriverView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        driver_id = request.data.get('driver_id')
        if not driver_id:
            return Response({"error": "Driver ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            driver = User.objects.get(pk=driver_id, role='driver')
        except User.DoesNotExist:
            return Response({"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)
            
        order.driver = driver
        order.status = 'assigned'
        order.save()
        
        return Response(OrderDetailSerializer(order).data)
class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Only admins can see all users
        if user.role == 'admin':
            return User.objects.all()
        return User.objects.none() 