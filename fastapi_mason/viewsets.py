"""
Base viewset classes for FastAPI Mason library.

These classes inherit from GenericViewSet and use mixins to add specific routes.
They are simple classes that combine the generic functionality with route mixins.
"""

from fastapi_mason.generics import GenericViewSet
from fastapi_mason.mixins import (
    CreateMixin,
    DestroyMixin,
    ListMixin,
    RetrieveMixin,
    UpdateMixin,
)
from fastapi_mason.types import ModelType


class ModelViewSet(
    GenericViewSet[ModelType],
    ListMixin[ModelType],
    RetrieveMixin[ModelType],
    CreateMixin[ModelType],
    UpdateMixin[ModelType],
    DestroyMixin[ModelType],
):
    """Base viewset providing full CRUD operations."""

    pass


class ReadOnlyViewSet(
    GenericViewSet[ModelType],
    ListMixin[ModelType],
    RetrieveMixin[ModelType],
):
    """Read-only viewset providing list and retrieve operations."""

    pass
