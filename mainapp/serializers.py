from rest_framework import serializers
from .models import Order, Stock
from users.serializers import UserSerializer

# mainapp/serializers.py
class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new order.
    """
    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'customer_phone', 
            'delivery_street', 'delivery_city', 'delivery_location',
            'item', 'quantity', 'status'
        ]

    def create(self, validated_data):
        # Set the seller as the current user
        validated_data['seller'] = self.context['request'].user
        
        # Check stock availability
        item = validated_data.get('item')
        quantity = validated_data.get('quantity', 1)
        seller = validated_data['seller']
        
        try:
            stock = Stock.objects.get(seller=seller, item_name=item)
            if stock.quantity < quantity:
                raise serializers.ValidationError(f"Insufficient stock for {item}. Available: {stock.quantity}")
        except Stock.DoesNotExist:
            raise serializers.ValidationError(f"Item {item} is not in your inventory.")
            
        return super().create(validated_data)


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for the Order model.
    """
    seller = UserSerializer(read_only=True)
    driver = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'seller', 'driver', 'customer_name', 'customer_phone',
            'delivery_street', 'delivery_city', 'delivery_location',
            'item', 'quantity', 'status',
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