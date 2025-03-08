from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Custom permission to allow only admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsSeller(permissions.BasePermission):
    """
    Custom permission to allow only seller users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'seller'
    
    def has_object_permission(self, request, view, obj):
        # For Order and Stock objects, allow only if the seller is the owner
        if hasattr(obj, 'seller'):
            return obj.seller == request.user
        return False


class IsDriver(permissions.BasePermission):
    """
    Custom permission to allow only driver users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'driver'
    
    def has_object_permission(self, request, view, obj):
        # For Order objects, allow only if the driver is assigned
        if hasattr(obj, 'driver'):
            return obj.driver == request.user
        return False


class IsAdminOrSellerOwner(permissions.BasePermission):
    """
    Custom permission to allow admins or the seller who owns the object.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == 'admin' or request.user.role == 'seller'
        )
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        if request.user.role == 'seller' and hasattr(obj, 'seller'):
            return obj.seller == request.user
        return False


class IsAdminOrAssignedDriver(permissions.BasePermission):
    """
    Custom permission to allow admins or the driver assigned to the order.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == 'admin' or request.user.role == 'driver'
        )
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        if request.user.role == 'driver' and hasattr(obj, 'driver'):
            return obj.driver == request.user
        return False