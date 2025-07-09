"""
Concrete pagination implementations for FastAPI+ library.

Provides ready-to-use pagination classes for different pagination strategies.
"""

import math
from abc import ABC, abstractmethod
from typing import Generic

from fastapi import Query
from pydantic import BaseModel
from tortoise.queryset import QuerySet

from fastapi_mason.types import T


class Pagination(ABC, BaseModel, Generic[T]):
    """
    Abstract base class for pagination implementations.

    All pagination classes should inherit from this class and implement
    the required abstract methods.
    """

    @classmethod
    @abstractmethod
    def from_query(cls, **kwargs) -> 'Pagination':
        """
        Create pagination instance from query parameters.

        Args:
            **kwargs: Query parameters

        Returns:
            Pagination instance
        """
        pass

    @abstractmethod
    def paginate(self, queryset: QuerySet[T]) -> QuerySet[T]:
        """
        Apply pagination to a queryset.

        Args:
            queryset: The queryset to paginate

        Returns:
            Paginated queryset
        """
        pass

    async def fill_meta(self, queryset: QuerySet[T]) -> None:
        """
        Fill pagination metadata (like total count, pages, etc.).

        This method is called after pagination to populate additional
        metadata that might be needed for the response.

        Args:
            queryset: Original (unpaginated) queryset
        """
        pass


# Concrete implementations


class DisabledPagination(Pagination[T]):
    """
    Pagination class that disables pagination.

    This class returns the entire queryset without any limits or offsets.
    Useful when pagination is not needed or should be disabled for specific endpoints.
    """

    @classmethod
    def from_query(cls) -> 'DisabledPagination':
        """Create instance without any query parameters."""
        return cls()

    def paginate(self, queryset: QuerySet[T]) -> QuerySet[T]:
        """Return the queryset unchanged."""
        return queryset


class LimitOffsetPagination(Pagination[T]):
    """
    Limit/Offset based pagination.

    This pagination style uses 'limit' and 'offset' parameters to control
    the number of items returned and how many to skip.

    Query parameters:
    - offset: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 10, max: 100)
    """

    offset: int = 0
    limit: int = 10
    total: int = 0

    @classmethod
    def from_query(
        cls,
        offset: int = Query(0, ge=0, description='Number of records to skip'),
        limit: int = Query(10, ge=1, le=100, description='Number of records to return'),
    ) -> 'LimitOffsetPagination':
        """Create instance from query parameters."""
        return cls(offset=offset, limit=limit)

    def paginate(self, queryset: QuerySet[T]) -> QuerySet[T]:
        """Apply limit and offset to the queryset."""
        return queryset.offset(self.offset).limit(self.limit)

    async def fill_meta(self, queryset: QuerySet[T]) -> None:
        """Fill total count metadata."""
        self.total = await queryset.count()


class PageNumberPagination(Pagination[T]):
    """
    Page number based pagination.

    This pagination style uses 'page' and 'size' parameters to control
    which page to return and how many items per page.

    Query parameters:
    - page: Page number to return (default: 1)
    - size: Number of records per page (default: 10, max: 100)
    """

    page: int = 1
    size: int = 10
    total: int = 0
    pages: int = 0

    @classmethod
    def from_query(
        cls,
        page: int = Query(1, ge=1, description='Page number'),
        size: int = Query(10, ge=1, le=100, description='Number of records per page'),
    ) -> 'PageNumberPagination':
        """Create instance from query parameters."""
        return cls(page=page, size=size)

    def paginate(self, queryset: QuerySet[T]) -> QuerySet[T]:
        """Apply pagination based on page number and size."""
        offset = (self.page - 1) * self.size
        return queryset.offset(offset).limit(self.size)

    async def fill_meta(self, queryset: QuerySet[T]) -> None:
        """Fill pagination metadata including total count and pages."""
        self.total = await queryset.count()
        self.pages = math.ceil(self.total / self.size) if self.size > 0 else 0


class CursorPagination(Pagination[T]):
    """
    Cursor based pagination.

    This pagination style uses a cursor (usually an ID or timestamp) to determine
    the starting point for the next page. This is more efficient for large datasets
    as it doesn't require counting all records.

    Query parameters:
    - cursor: The cursor value to start from
    - size: Number of records per page (default: 10, max: 100)
    """

    cursor: str | None = None
    size: int = 10
    next_cursor: str | None = None
    previous_cursor: str | None = None
    has_next: bool = False
    has_previous: bool = False

    # Configuration
    cursor_field: str = 'id'  # Field to use for cursor
    ordering: str = 'asc'  # 'asc' or 'desc'

    @classmethod
    def from_query(
        cls,
        cursor: str | None = Query(None, description='Cursor for pagination'),
        size: int = Query(10, ge=1, le=100, description='Number of records per page'),
    ) -> 'CursorPagination':
        """Create instance from query parameters."""
        return cls(cursor=cursor, size=size)

    def get_cursor_field(self) -> str:
        """Get the field name used for cursor pagination."""
        return self.cursor_field

    def encode_cursor(self, obj: T) -> str:
        """
        Encode cursor from model instance.

        Args:
            obj: Model instance

        Returns:
            Encoded cursor string
        """
        field_value = getattr(obj, self.get_cursor_field())
        return str(field_value)

    def decode_cursor(self, cursor_str: str) -> any:
        """
        Decode cursor string to field value.

        Args:
            cursor_str: Cursor string

        Returns:
            Decoded cursor value
        """
        if not cursor_str:
            return None

        try:
            # Try to convert to int first (most common case for ID fields)
            return int(cursor_str)
        except (ValueError, TypeError):
            # If not int, return as string
            return cursor_str

    def paginate(self, queryset: QuerySet[T]) -> QuerySet[T]:
        """
        Apply cursor-based pagination.

        Args:
            queryset: The queryset to paginate

        Returns:
            Paginated queryset
        """
        cursor_field = self.get_cursor_field()

        # Apply cursor filter if provided
        if self.cursor:
            cursor_value = self.decode_cursor(self.cursor)
            if cursor_value is not None:
                if self.ordering == 'desc':
                    # For descending order, get records less than cursor
                    queryset = queryset.filter(**{f'{cursor_field}__lt': cursor_value})
                else:
                    # For ascending order, get records greater than cursor
                    queryset = queryset.filter(**{f'{cursor_field}__gt': cursor_value})

        # Apply ordering
        if self.ordering == 'desc':
            queryset = queryset.order_by(f'-{cursor_field}')
        else:
            queryset = queryset.order_by(cursor_field)

        # Get one extra record to check if there's a next page
        return queryset.limit(self.size + 1)

    async def fill_meta(self, queryset: QuerySet[T]) -> None:
        """
        Fill cursor metadata.

        This method is called after pagination to populate cursor information
        for next/previous page navigation.

        Args:
            queryset: Original (unpaginated) queryset
        """
        # Get the paginated results to determine cursor metadata
        paginated_query = self.paginate(queryset)
        results = await paginated_query

        if not results:
            self.has_next = False
            self.has_previous = bool(self.cursor)
            self.next_cursor = None
            self.previous_cursor = None
            return

        # Check if we have more results than requested (indicates next page exists)
        self.has_next = len(results) > self.size

        # Set next cursor from the last item (excluding the extra item)
        if self.has_next:
            last_item = results[self.size - 1]  # Last item in the actual page
            self.next_cursor = self.encode_cursor(last_item)
        else:
            self.next_cursor = None

        # For previous cursor, we need to check if current cursor exists
        self.has_previous = bool(self.cursor)

        if self.has_previous and results:
            # For previous cursor, we would need to do a reverse query
            # This is a simplified implementation
            first_item = results[0]

            # Check if there are records before the first item
            cursor_field = self.get_cursor_field()
            first_cursor_value = getattr(first_item, cursor_field)

            if self.ordering == 'desc':
                prev_query = queryset.filter(**{f'{cursor_field}__gt': first_cursor_value})
                prev_query = prev_query.order_by(cursor_field).limit(1)
            else:
                prev_query = queryset.filter(**{f'{cursor_field}__lt': first_cursor_value})
                prev_query = prev_query.order_by(f'-{cursor_field}').limit(1)

            prev_results = await prev_query
            if prev_results:
                self.previous_cursor = self.encode_cursor(prev_results[0])
            else:
                self.previous_cursor = None
        else:
            self.previous_cursor = None
