from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from users.serializers import UserSerializer

from .models import  Order, Stock
from .serializers import (
    OrderCreateSerializer, OrderDetailSerializer,
    OrderStatusUpdateSerializer, StockSerializer
)
from .permissions import (
    IsAdmin, IsAdminSeller, IsSeller, IsDriver,
    IsAdminOrSellerOwner, IsAdminOrAssignedDriver
)

from django.contrib.auth import get_user_model
User = get_user_model()







class OrderListCreateView(generics.ListCreateAPIView):
    """
    API endpoint that allows orders to be viewed or created.
    GET: Admins can see all orders. Sellers can only see their own orders.
    POST: Admins can create orders for any seller. Sellers can only create their own orders.
    """
    permission_classes = [IsAuthenticated, IsAdminSeller]
    
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
    filterset_fields = ['status', 'created_at', 'delivery_city', 'customer_name']

    def perform_create(self, serializer):
        """
        Override to allow admins to create orders for any seller.
        Sellers can only create orders for themselves.
        """
        user = self.request.user
        
        # If seller_id is provided in request data and user is admin
        if user.role == 'admin' and 'seller_id' in self.request.data:
            try:
                seller_id = int(self.request.data['seller_id'])
                seller = User.objects.get(id=seller_id, role='seller')
                serializer.save(seller=seller)
            except (User.DoesNotExist, ValueError):
                # Fall back to using the admin as seller if seller_id is invalid
                serializer.save(seller=user)
        else:
            # Default behavior - use current user as seller
            serializer.save(seller=user)


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
    pagination_class = None #uncomment this line to disable pagination
    
    def get_queryset(self):
        return Order.objects.filter(driver=self.request.user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that allows a single order to be viewed, updated, or deleted.
    GET: Admins can see any order. Sellers can only see their own orders.
         Drivers can only see orders assigned to them.
    PUT/PATCH: Admins can update any order. Sellers can update their own orders' details (not status).
    DELETE: Only admins can delete orders.
    """
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        elif user.role == 'seller':
            return Order.objects.filter(seller=user)
        elif user.role == 'driver':
            return Order.objects.filter(driver=user)
        return Order.objects.none()
    
    def get_permissions(self):
        """
        Custom permission handling based on request method.
        """
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdmin()]
        elif self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), IsAdminOrSellerOwner()]
        return [IsAuthenticated()]
    
    def update(self, request, *args, **kwargs):
        """
        Custom update handling to prevent sellers from changing order status.
        Only allow status updates through the dedicated OrderStatusUpdateView.
        """
        if request.user.role == 'seller' and 'status' in request.data:
            return Response(
                {"error": "Sellers cannot update order status. Contact an admin."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)


class OrderStatusUpdateView(APIView):
    """
    API endpoint that allows updating the status of an order.
    - Admins can update any order's status
    - Assigned drivers can only update their assigned orders' status
    - Sellers cannot update status (they must go through admin)
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
        
        # Validate that drivers can only update to certain statuses
        if request.user.role == 'driver':
            allowed_statuses = ['in_transit', 'delivered', 'no_answer', 'postponed']
            requested_status = request.data.get('status')
            
            if requested_status not in allowed_statuses:
                return Response(
                    {"error": f"Drivers can only update to these statuses: {', '.join(allowed_statuses)}"},
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
    POST: Admins can create stock for any seller. Sellers can only create their own stock.
    """
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated, IsAdminSeller]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Stock.objects.all()
        elif user.role == 'seller':
            return Stock.objects.filter(seller=user)
        return Stock.objects.none()
    
    def perform_create(self, serializer):
        """
        Override to allow admins to create stock for any seller.
        Sellers can only create stock for themselves.
        """
        user = self.request.user
        
        # If seller_id is provided in request data and user is admin
        if user.role == 'admin' and 'seller_id' in self.request.data:
            try:
                seller_id = int(self.request.data['seller_id'])
                seller = User.objects.get(id=seller_id, role='seller')
                serializer.save(seller=seller)
            except (User.DoesNotExist, ValueError):
                # Fall back to using the admin as seller if seller_id is invalid
                serializer.save(seller=user)
        else:
            # Default behavior - use current user as seller
            serializer.save(seller=user)


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
            # This is the important line - add the role filter
            driver = User.objects.get(pk=driver_id, role='driver')
        except User.DoesNotExist:
            return Response({"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)
            
        order.driver = driver
        order.status = 'assigned'
        order.save()
        
        return Response(OrderDetailSerializer(order).data)
class UserListView(generics.ListAPIView):
    """
    API endpoint for listing users.
    GET: Admin can see all users, sellers and drivers can see only themselves.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        # Other users can only see themselves
        return User.objects.filter(id=user.id)
    


class OrderFilter(filters.FilterSet):
    min_date = filters.DateFilter(field_name="created_at", lookup_expr='gte')
    max_date = filters.DateFilter(field_name="created_at", lookup_expr='lte')
    
    class Meta:
        model = Order
        fields = ['status', 'delivery_city', 'min_date', 'max_date']

class ApproveStockView(APIView):
    """
    API endpoint for admins to approve stock items.
    Only admins can access this endpoint.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, pk):
        try:
            stock = Stock.objects.get(pk=pk)
        except Stock.DoesNotExist:
            return Response({"error": "Stock item not found"}, status=status.HTTP_404_NOT_FOUND)
        
        stock.approved = True
        stock.save()
        
        return Response(StockSerializer(stock).data)