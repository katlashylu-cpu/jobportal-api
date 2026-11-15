from rest_framework import permissions


class IsCandidate(permissions.BasePermission):
    """Allows access only to candidate users."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'candidate'
        )


class IsRecruiter(permissions.BasePermission):
    """Allows access only to recruiter users."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'recruiter'
        )


class IsAdmin(permissions.BasePermission):
    """Allows access only to admin / staff users."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'role', None) == 'admin'
                or request.user.is_staff
                or request.user.is_superuser
            )
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to allow read-only access for safe methods,
    and write access only to the object owner.
    Supports objects with .owner attribute (e.g. Company) or .company.owner (e.g. Job).
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'company') and hasattr(obj.company, 'owner'):
            return obj.company.owner == request.user
        if hasattr(obj, 'candidate'):
            return obj.candidate == request.user

        return False
