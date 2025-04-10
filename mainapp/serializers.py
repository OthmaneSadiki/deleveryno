from django.forms import ValidationError
from rest_framework import serializers

from users.serializers import UserSerializer
from .models import Order, Stock, Message
from django.contrib.auth import get_user_model
User = get_user_model()


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
# In mainapp/serializers.py - Fix the OrderCreateSerializer

class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new order.
    """
    seller_id = serializers.IntegerField(required=False, write_only=True)
    delivery_location = serializers.CharField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True) # New comment field
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'customer_phone', 
            'delivery_street', 'delivery_city', 'delivery_location',
            'item', 'quantity', 'status', 'seller_id', 'comment'
        ]
        
    def validate_delivery_location(self, value):
        """Validate that delivery_location is a proper Google Maps URL if provided."""
        return validate_google_maps_url(value)

    def validate(self, data):
        """
        Validate the order data including stock availability.
        """
        request = self.context['request']
        user = request.user
        
        # Determine the seller
        seller = None
        if user.role == 'admin' and 'seller_id' in data:
            try:
                seller_id = data['seller_id']
                seller = User.objects.get(id=seller_id, role='seller')
            except (User.DoesNotExist, ValueError):
                raise serializers.ValidationError("Invalid seller selected")
        else:
            seller = user
            
        # Check stock availability if we have a valid seller
        item = data.get('item')
        quantity = data.get('quantity', 1)
        
        try:
            stock = Stock.objects.get(seller=seller, item_name=item)
            
            # Check if stock is approved
            if not stock.approved:
                raise serializers.ValidationError(f"Item {item} is pending approval and cannot be used yet.")
            
            # Check quantity
            if stock.quantity < quantity:
                raise serializers.ValidationError(f"Insufficient stock for {item}. Available: {stock.quantity}")
                
        except Stock.DoesNotExist:
            raise serializers.ValidationError(f"Item '{item}' is not in the selected seller's inventory.")
        
        return data
    
    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        
        # Handle seller assignment
        if user.role == 'admin' and 'seller_id' in validated_data:
            seller_id = validated_data.pop('seller_id')
            try:
                seller = User.objects.get(id=seller_id, role='seller')
                validated_data['seller'] = seller
            except (User.DoesNotExist, ValueError):
                validated_data['seller'] = user
        else:
            validated_data['seller'] = user
            
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
            'item', 'quantity', 'status', 'comment',
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
        

# Add this to mainapp/serializers.py after the existing serializers

class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Message model.
    """
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    recipient_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'recipient', 'recipient_id', 'subject', 
            'content', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        # Get current user (sender)
        sender = self.context['request'].user
        
        # Handle recipient selection based on user role
        if 'recipient_id' not in validated_data:
            if sender.role in ['seller', 'driver']:
                # For sellers and drivers, send to the first admin
                try:
                    admin_user = User.objects.filter(role='admin').first()
                    if not admin_user:
                        raise serializers.ValidationError("No admin user found to send message to")
                    validated_data['recipient'] = admin_user
                except User.DoesNotExist:
                    raise serializers.ValidationError("No admin user found to send message to")
            else:
                # For admins, require explicit recipient
                raise serializers.ValidationError("Recipient is required for admin messages")
        else:
            recipient_id = validated_data.pop('recipient_id')
            try:
                recipient = User.objects.get(id=recipient_id)
                validated_data['recipient'] = recipient
            except User.DoesNotExist:
                raise serializers.ValidationError("Recipient not found")
        
        # Set the sender
        validated_data['sender'] = sender
        
        return super().create(validated_data)