"""
Example custom viewsets using the new FastAPI+ library architecture.

This demonstrates how to use the restructured library with GenericViewSet
and route mixins.
"""

from typing import TypeVar

from tortoise import Model
from tortoise.contrib.pydantic import PydanticModel

from app.fastapi_plus import (
    CreateMixin,
    CreateOnlyViewSet,
    GenericViewSet,
    LimitOffsetPagination,
    ListCreateViewSet,
    ListMixin,
    ModelViewSet,
    PageNumberPagination,
    PaginatedResponseDataWrapper,
    ReadOnlyViewSet,
    RetrieveMixin,
    StatusResponseWrapper,
)

ModelType = TypeVar('ModelType', bound=Model)
SchemaType = TypeVar('SchemaType', bound=PydanticModel)


class CustomViewSet(ModelViewSet):
    """
    Custom viewset with page number pagination and response wrapper.

    This viewset provides all CRUD operations with:
    - Page number pagination (page, size parameters)
    - Paginated response wrapper that includes metadata
    """

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper


class CustomReadOnlyViewSet(ReadOnlyViewSet):
    """
    Custom read-only viewset with limit-offset pagination.

    This viewset provides only list and retrieve operations with:
    - Limit-offset pagination (limit, offset parameters)
    - Status response wrapper for consistent API responses
    """

    pagination = LimitOffsetPagination
    single_wrapper = StatusResponseWrapper


class CustomGenericViewSet(GenericViewSet):
    """
    Custom viewset inheriting directly from GenericViewSet.

    This allows for maximum flexibility - you can add any combination
    of routes by calling the appropriate mixin methods.
    """

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper

    def __init__(self):
        """Initialize with custom route configuration."""
        super().__init__()

        # Only add the routes we want
        # This creates a viewset with list and create only
        if hasattr(self, 'add_list_route'):
            ListMixin.add_list_route(self)
        if hasattr(self, 'add_create_route'):
            CreateMixin.add_create_route(self)

        self.finalize_routes()


class MixedViewSet(GenericViewSet, ListMixin, CreateMixin, RetrieveMixin):
    """
    Custom viewset using individual mixins with GenericViewSet.

    This demonstrates how to build custom viewsets by combining
    GenericViewSet with specific mixins.
    Provides: list, create, retrieve (no update/delete)
    """

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper

    def __init__(self):
        """Initialize and add routes from mixins."""
        super().__init__()

        # Add routes from each mixin
        self.add_list_route()
        self.add_create_route()
        self.add_retrieve_route()

        self.finalize_routes()


class SimpleCreateOnlyViewSet(CreateOnlyViewSet):
    """
    Simple create-only viewset.

    Just inherits from CreateOnlyViewSet - no additional configuration needed.
    """

    pass


class CustomListCreateViewSet(ListCreateViewSet):
    """
    Custom list and create viewset with specific wrappers.
    """

    pagination = LimitOffsetPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = StatusResponseWrapper
