# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

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
    """
    API endpoint for user login.
    Validates the provided username and password. If authentication is successful and the user is approved,
    an authentication token is returned along with the user details.
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                # Optionally enforce that the user must be approved by an admin.
                if not user.approved and user.role != 'admin':
                    return Response({"error": "User not approved by admin."},
                                    status=status.HTTP_403_FORBIDDEN)
                # Generate or retrieve the token for this user.
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key,
                    "user": UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API endpoint for retrieving and updating the current user's profile.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            # Don't allow changing role or approval status via this endpoint
            if 'role' in serializer.validated_data:
                del serializer.validated_data['role']
            if 'approved' in serializer.validated_data:
                del serializer.validated_data['approved']
                
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