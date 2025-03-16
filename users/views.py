# users/views.py
from urllib import request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework import generics

from .models import User
from .serializers import (
    SellerRegistrationSerializer,
    DriverRegistrationSerializer,
    LoginSerializer,
    UserSerializer
)
from mainapp.permissions import IsAdmin

class SellerRegistrationView(APIView):
    """
    API endpoint for seller registration.
    Expects fields: username, email, password, first_name, last_name, phone, city.
    The role is automatically set to 'seller'.
    """
    def post(self, request):
        serializer = SellerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Serialize the created user (excluding sensitive data)
            user_serializer = UserSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DriverRegistrationView(APIView):
    """
    API endpoint for driver registration.
    Expects similar fields to seller registration. The role is automatically set to 'driver'.
    """
    def post(self, request):
        serializer = DriverRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_serializer = UserSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Use the authenticate function with email parameter
        user = authenticate(request=request, email=email, password=password)
        
        if user:
            if not user.approved and user.role != 'admin':
                return Response({"error": "User not approved by admin."},
                            status=status.HTTP_403_FORBIDDEN)
            
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response({"error": "Invalid credentials"}, 
                      status=status.HTTP_401_UNAUTHORIZED)

class UserProfileView(APIView):
    """
    API endpoint for retrieving and updating the current user's profile.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
    # Use a context manager to track if role is changing
        role_changing = False
        current_role = request.user.role
        if 'role' in request.data and request.data['role'] != current_role:
            role_changing = True
    
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            # Don't allow changing role or approval status via this endpoint
            if 'role' in serializer.validated_data:
                del serializer.validated_data['role']
            if 'approved' in serializer.validated_data:
                del serializer.validated_data['approved']
        
            # Remove rib field if the user is not a seller
            if current_role != 'seller' and 'rib' in serializer.validated_data:
                del serializer.validated_data['rib']
            
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApproveUserView(APIView):
    """
    API endpoint for admins to approve users.
    Only admins can access this endpoint.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        user.approved = True
        user.save()
        
        return Response(UserSerializer(user).data)

# Add this to users/views.py
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
    
class DebugView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'username': user.username,
            'role': user.role,
            'is_authenticated': user.is_authenticated,
            'approved': user.approved,
            'user_id': user.id,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        })
    
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for admins to manage users.
    GET: Retrieve a specific user
    PUT/PATCH: Update user details
    DELETE: Delete a user
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    def update(self, request, *args, **kwargs):
        print("Received data:", request.data)  # Debug statement - this shows the incoming data
        
        # Call the parent implementation to continue normal processing
        return super().update(request, *args, **kwargs)
        
    def perform_update(self, serializer):
        
        # Get the current user role
        instance = self.get_object()
        current_role = instance.role
        new_role = serializer.validated_data.get('role', current_role)
    
        # If changing from seller to non-seller, remove the RIB
        if current_role == 'seller' and new_role != 'seller':
            instance.rib = ''
        
        # If role is not seller and RIB is in the data, remove it
        if new_role != 'seller' and 'rib' in serializer.validated_data:
            serializer.validated_data.pop('rib')
        
        serializer.save()