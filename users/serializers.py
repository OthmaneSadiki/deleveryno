
import uuid
from rest_framework import serializers
from .models import User

class BaseRegistrationSerializer(serializers.ModelSerializer):
    """Base serializer for user registration with auto-username generation."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    # Make username optional
    username = serializers.CharField(required=False)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'phone', 'city']

    def create(self, validated_data):
        # Generate username if not provided
        if 'username' not in validated_data or not validated_data['username']:
            email_prefix = validated_data['email'].split('@')[0]
            # Create a unique username based on email prefix
            base_username = email_prefix[:15]  # Limit length
            username = base_username
            
            # Check if username exists and append random string if needed
            counter = 1
            while User.objects.filter(username=username).exists():
                # Generate a shorter unique suffix
                suffix = str(uuid.uuid4())[:8]
                username = f"{base_username[:10]}_{suffix}"
                counter += 1
                if counter > 10:  # Avoid infinite loop
                    username = f"user_{str(uuid.uuid4())[:10]}"
                    break
                    
            validated_data['username'] = username
            
        return super().create(validated_data)

class SellerRegistrationSerializer(BaseRegistrationSerializer):
    def create(self, validated_data):
        validated_data['role'] = 'seller'
        return super().create(validated_data)


class DriverRegistrationSerializer(BaseRegistrationSerializer):
    def create(self, validated_data):
        validated_data['role'] = 'driver'
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    A general serializer for representing a user.
    
    This serializer is useful for returning user details (for example,
    after login or in a profile view). It includes fields that describe
    the user's identity, contact information, role, and approval status.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'city', 'role', 'approved']


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    This serializer is used to validate login credentials. It requires
    the username and password (which is write-only for security).
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )


