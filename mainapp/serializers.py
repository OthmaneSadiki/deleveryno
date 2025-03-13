from rest_framework import serializers
from .models import Order, Stock
from users.serializers import UserSerializer

# mainapp/serializers.py
class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new order.
    """
    seller_id = serializers.IntegerField(required=False, write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'customer_phone', 
            'delivery_street', 'delivery_city', 'delivery_location',
            'item', 'quantity', 'status', 'seller_id'
        ]

    def create(self, validated_data):
        # Remove seller_id if present as it's handled in the view
        if 'seller_id' in validated_data:
            validated_data.pop('seller_id')
        
        # If seller is not set in validated_data, use request user (default behavior)
        if 'seller' not in validated_data:
            validated_data['seller'] = self.context['request'].user
            
        # Get seller for stock check
        seller = validated_data['seller']
        
        # Check stock availability
        item = validated_data.get('item')
        quantity = validated_data.get('quantity', 1)
        
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
    seller_id = serializers.IntegerField(required=False, write_only=True)
    seller = UserSerializer(read_only=True)
    
    class Meta:
        model = Stock
        fields = ['id', 'seller', 'seller_id', 'item_name', 'quantity']