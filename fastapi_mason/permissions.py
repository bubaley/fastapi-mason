"""
Permission system for FastAPI+ viewsets.

Provides permission classes and utilities for access control,
similar to Django REST Framework permissions.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Type

from fastapi import HTTPException, Request


class BasePermission(ABC):
    """
    Abstract base class for all permission classes.

    Permission classes are used to grant or deny access to viewset actions.
    They can check user authentication, authorization, object ownership, etc.
    """

    @abstractmethod
    def has_permission(self, request: Request, view: Any) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.

        This method is called for all actions to check general permissions.

        Args:
            request: The FastAPI request object
            view: The viewset instance

        Returns:
            True if permission granted, False otherwise
        """
        pass

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """
        Return `True` if permission is granted for the specific object, `False` otherwise.

        This method is called for object-level actions (retrieve, update, delete).

        Args:
            request: The FastAPI request object
            view: The viewset instance
            obj: The object being accessed

        Returns:
            True if permission granted, False otherwise
        """
        # By default, object permissions match general permissions
        return self.has_permission(request, view)


# Built-in permission classes


class AllowAny(BasePermission):
    """
    Allow any access.
    This permission is not restrictive at all.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Always allow access."""
        return True


class DenyAll(BasePermission):
    """
    Deny all access.
    This permission is always restrictive.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Always deny access."""
        return False


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.

    Requires that request.state.user exists and is not None.
    You need to set up authentication middleware to populate request.state.user.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Check if user is authenticated."""
        user = getattr(request.state, 'user', None)
        return user is not None and getattr(user, 'is_authenticated', True)


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.

    Requires that request.state.user exists and has is_admin=True or is_staff=True.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Check if user is admin."""
        user = getattr(request.state, 'user', None)
        if not user:
            return False

        return (
            getattr(user, 'is_admin', False) or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)
        )


class IsOwner(BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.

    Assumes the model instance has an `owner` field that points to a user.
    You can customize the owner field by subclassing and overriding get_owner_field().
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Allow all authenticated users to access the list."""
        user = getattr(request.state, 'user', None)
        return user is not None

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Only allow owners to access their objects."""
        user = getattr(request.state, 'user', None)
        if not user:
            return False

        owner_field = self.get_owner_field()
        obj_owner = getattr(obj, owner_field, None)

        # Handle different ways of comparing users
        if hasattr(user, 'id') and hasattr(obj_owner, 'id'):
            return user.id == obj_owner.id

        return user == obj_owner

    def get_owner_field(self) -> str:
        """Get the field name that contains the owner reference."""
        return 'owner'


class IsOwnerOrReadOnly(IsOwner):
    """
    Object-level permission to allow read access to any user,
    but only allow write access to the owner of the object.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Allow all users to access the list."""
        return True

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Allow read access to all, write access only to owner."""
        # Read permissions for any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Write permissions only for owner
        return super().has_object_permission(request, view, obj)


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allows read-only access to any user, and full access to authenticated users.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Allow read access to all, write access to authenticated users."""
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        user = getattr(request.state, 'user', None)
        return user is not None and getattr(user, 'is_authenticated', True)


# Permission utilities


def check_permissions(
    permission_classes: List[Type[BasePermission]], request: Request, view: Any, obj: Any = None
) -> None:
    """
    Check all permissions and raise HTTP 403 if any permission is denied.

    Args:
        permission_classes: List of permission classes to check
        request: FastAPI request object
        view: Viewset instance
        obj: Object being accessed (for object-level permissions)

    Raises:
        HTTPException: 403 Forbidden if any permission is denied
    """
    for permission_class in permission_classes:
        permission = permission_class()

        # Check general permissions
        if not permission.has_permission(request, view):
            raise HTTPException(status_code=403, detail=f'Permission denied by {permission_class.__name__}')

        # Check object-level permissions if object is provided
        if obj is not None:
            if not permission.has_object_permission(request, view, obj):
                raise HTTPException(status_code=403, detail=f'Object permission denied by {permission_class.__name__}')


def get_user_from_request(request: Request) -> Any:
    """
    Extract user from request state.

    This is a utility function that different authentication backends can use
    to get the current user from the request.

    Args:
        request: FastAPI request object

    Returns:
        User object or None if not authenticated
    """
    return getattr(request.state, 'user', None)
