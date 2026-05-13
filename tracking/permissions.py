from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == 'admin'


class IsAdminOrAssignedDriver(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        if request.user.role == 'driver':
            if hasattr(obj, 'driver'):
                return obj.driver == request.user
            if hasattr(obj, 'truck'):
                return obj.truck.driver == request.user
        return False
