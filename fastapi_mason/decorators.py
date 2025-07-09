"""
Decorators for FastAPI+ viewsets.

Provides decorators for automatic viewset registration and configuration.
"""

from typing import Any, Callable, Optional, Type

from fastapi import APIRouter

from fastapi_mason.types import SchemaType


def viewset(router: APIRouter):
    """
    Decorator for automatic viewset registration with FastAPI router.

    This decorator automatically binds viewset methods to the provided router
    without modifying function signatures, making it more robust and reliable.

    Args:
        router: FastAPI router to register viewset routes with

    Returns:
        Decorated viewset class

    Example:
        ```python
        from fastapi import APIRouter
        from app.fastapi_plus import ModelViewSet, viewset

        router = APIRouter(prefix="/users")

        @viewset(router)
        class UserViewSet(ModelViewSet[User]):
            model = User
            read_schema = UserRead
            create_schema = UserCreate
            update_schema = UserUpdate
        ```
    """

    def decorator(cls: Type[Any]) -> Type[Any]:
        """Apply viewset decorator to class."""
        # Store router on the class
        cls.router = router

        try:
            # Create instance to trigger route registration
            cls()

        except Exception as e:
            raise RuntimeError(
                f'Failed to initialize viewset {cls.__name__}: {e}. '
                f'Make sure all required attributes (model, schemas) are set.'
            ) from e

        return cls

    return decorator


def action(
    methods: Optional[list[str]] = None,
    detail: bool = False,
    path: Optional[str] = None,
    name: Optional[str] = None,
    response_model: Optional[SchemaType | list[SchemaType]] = None,
    **kwargs,
):
    """
    Decorator to mark a viewset method as a routable action.

    Similar to Django REST Framework's @action decorator.

    Args:
        methods: List of HTTP methods (default: ['GET'])
        detail: Whether this is a detail action (requires object ID)
        url_path: Custom URL path for the action
        url_name: Custom name for the route
        override_existing: Whether to override existing routes with same path
        **kwargs: Additional route options

    Example:
        ```python
        @viewset(router)
        class UserViewSet(ModelViewSet[User]):
            model = User

            @action(methods=['POST'], detail=True)
            async def set_password(self, item_id: int, password: str):
                user = await self.get_object(item_id)
                # ... set password logic
                return {"message": "Password updated"}

            @action(methods=['GET'], detail=False, url_path='active')
            async def active_users(self):
                # ... get active users logic
                return await self.get_queryset().filter(is_active=True)

            # Override the default list endpoint
            @action(methods=['GET'], detail=False, url_path='', override_existing=True)
            async def custom_list(self, request: Request):
                # Custom list logic
                return {"custom": "response"}
        ```
    """
    if methods is None:
        methods = ['GET']

    def decorator(func: Callable) -> Callable:
        # Store action metadata on the function
        func._is_action = True
        func._action_methods = [method.upper() for method in methods]
        func._action_detail = detail
        # func._action_path = path or func.__name__.replace("_", "-")
        func._action_path = path
        func._action_name = name
        func._action_response_model = response_model
        func._action_kwargs = kwargs

        return func

    return decorator
