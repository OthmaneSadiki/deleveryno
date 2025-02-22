
from rest_framework import serializers
from .models import User

class SellerRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a seller.
    
    The seller provides details such as username, email, password,
    first name, last name, phone, and city. The role is automatically
    set to "seller". The password field is write-only and will be hashed
    when the user is created.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'phone', 'city']

    def create(self, validated_data):
        # Force the role to be 'seller'
        validated_data['role'] = 'seller'
        # Create the user using Django's create_user method, which hashes the password.
        user = User.objects.create_user(**validated_data)
        return user


class DriverRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a driver.
    
    Similar to the SellerRegistrationSerializer, it takes in the registration
    details and forces the role to "driver". The password field is write-only.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'phone', 'city']

    def create(self, validated_data):
        # Force the role to be 'driver'
        validated_data['role'] = 'driver'
        user = User.objects.create_user(**validated_data)
        return user


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
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
