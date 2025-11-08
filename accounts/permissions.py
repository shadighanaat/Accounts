from rest_framework.permissions import BasePermission
from accounts.models import CustomUser

class IsOwnerUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and user.__class__.__name__ == 'CustomUser'

    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'user') and obj.user == request.user


class IsOwnerMarketer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and user.__class__.__name__ == 'Marketer'

    def has_object_permission(self, request, view, obj):
        return obj.pk == request.user.pk
        