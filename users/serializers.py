
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
        
        # Extract password to hash it properly
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # This properly hashes the password
        user.save()
        return user

class SellerRegistrationSerializer(BaseRegistrationSerializer):
    # Add RIB field specifically for sellers
    rib = serializers.CharField(required=False, allow_blank=True)
    
    class Meta(BaseRegistrationSerializer.Meta):
        # Extend the fields list to include RIB
        fields = BaseRegistrationSerializer.Meta.fields + ['rib']
    
    def create(self, validated_data):
        validated_data['role'] = 'seller'
        # Rest of your create method remains the same
        return super().create(validated_data)


class DriverRegistrationSerializer(BaseRegistrationSerializer):
    def create(self, validated_data):
        validated_data['role'] = 'driver'
        return super().create(validated_data)


# Modify your UserSerializer to properly handle RIB field
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'city', 'role', 'approved', 'rib']
        read_only_fields = ['date_joined', 'updated_at'] 
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Add RIB field only for sellers
        if instance.role == 'seller':
            ret['rib'] = instance.rib
        return ret
        
    def update(self, instance, validated_data):
        # Make sure this method returns the instance!
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.city = validated_data.get('city', instance.city)
        instance.role = validated_data.get('role', instance.role)
        
        # Handle RIB field for sellers
        if instance.role == 'seller' and 'rib' in validated_data:
            instance.rib = validated_data.get('rib', instance.rib)
            
        instance.save()
        return instance
        


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


