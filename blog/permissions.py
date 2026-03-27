from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение: только админ может изменять, остальные только читают"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsAdminOrOwner(permissions.BasePermission):
    """Разрешение: админ или владелец объекта"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user and request.user.is_staff:
            return True

        if hasattr(obj, 'author'):
            return obj.author == request.user
        return obj == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Разрешение: владелец может изменять, остальные только читают"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'author'):
            return obj.author == request.user
        return obj == request.user
