from rest_framework import serializers
from .models import Address, Order, Stock
from users.serializers import UserSerializer

class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer for the Address model.
    """
    class Meta:
        model = Address
        fields = ['id', 'street', 'city']


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new order.
    """
    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'customer_phone', 'delivery_address',
            'item', 'quantity', 'status'
        ]

    def create(self, validated_data):
        # Set the seller as the current user
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for the Order model, including related fields.
    """
    seller = UserSerializer(read_only=True)
    driver = UserSerializer(read_only=True)
    delivery_address = AddressSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'seller', 'driver', 'customer_name', 'customer_phone',
            'delivery_address', 'item', 'quantity', 'status',
            'created_at', 'updated_at'
        ]


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the status of an order.
    """
    class Meta:
        model = Order
        fields = ['status']


class StockSerializer(serializers.ModelSerializer):
    """
    Serializer for the Stock model.
    """
    class Meta:
        model = Stock
        fields = ['id', 'item_name', 'quantity']
    
    def create(self, validated_data):
        # Set the seller as the current user
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)