from django.forms import ValidationError
from rest_framework import serializers

from users.serializers import UserSerializer
from .models import Order, Stock


def validate_google_maps_url(value):
    """Validator to ensure the URL is a valid Google Maps link if provided."""
    # Allow blank/empty values since the field is optional
    if not value or value.strip() == '':
        return value
        
    # Only validate if a value is actually provided
    if not (
        value.startswith('https://www.google.com/maps') or 
        value.startswith('https://goo.gl/maps') or 
        value.startswith('https://maps.app.goo.gl') or
        value.startswith('https://maps.google.com')
    ):
        raise ValidationError(
            'Please provide a valid Google Maps link (e.g., https://www.google.com/maps/...)'
        )
    return value

# mainapp/serializers.py
class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new order.
    """
    seller_id = serializers.IntegerField(required=False, write_only=True)
    delivery_location = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'customer_phone', 
            'delivery_street', 'delivery_city', 'delivery_location',
            'item', 'quantity', 'status', 'seller_id'
        ]
    def validate_delivery_location(self, value):
        """Validate that delivery_location is a proper Google Maps URL if provided."""
        return validate_google_maps_url(value)

    def create(self, validated_data):
        # Remove seller_id if present as it's handled in the view
        if 'seller_id' in validated_data:
            validated_data.pop('seller_id')
    
        # If seller is not set in validated_data, use request user (default behavior)
        if 'seller' not in validated_data:
            validated_data['seller'] = self.context['request'].user
        
        # Get seller for stock check
        seller = validated_data['seller']
    
        # Check stock availability and approval
        item = validated_data.get('item')
        quantity = validated_data.get('quantity', 1)
    
        try:
            stock = Stock.objects.get(seller=seller, item_name=item)
        
            # Check if stock is approved
            if not stock.approved:
                raise serializers.ValidationError(f"Item {item} is pending approval and cannot be used yet.")
            
            # Check quantity
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
        fields = ['id', 'seller', 'seller_id', 'item_name', 'quantity', 'approved', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def update(self, instance, validated_data):
        # If the user is an admin, don't un-approve when updating quantity or name
        request = self.context.get('request')
        if request and request.user.role == 'admin':
            # Admins can update without changing approval status
            instance.item_name = validated_data.get('item_name', instance.item_name)
            instance.quantity = validated_data.get('quantity', instance.quantity)
            instance.save()
            return instance
        else:
            # For sellers, any update (including quantity) requires re-approval
            instance.approved = False
            return super().update(instance, validated_data)