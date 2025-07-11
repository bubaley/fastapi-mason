"""
Concrete pagination implementations for FastAPI Mason library.

Provides ready-to-use pagination classes for different pagination strategies.
"""

import math
from abc import ABC, abstractmethod
from typing import Any, Generic

from fastapi import Query
from pydantic import BaseModel
from tortoise.queryset import QuerySet

from fastapi_mason.types import ModelType


class Pagination(ABC, BaseModel, Generic[ModelType]):
    """Abstract base class for pagination implementations."""

    @classmethod
    @abstractmethod
    def from_query(cls, **kwargs) -> 'Pagination':
        """Create pagination instance from query parameters."""
        pass

    @abstractmethod
    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        """Apply pagination to a queryset."""
        pass

    async def fill_meta(self, queryset: QuerySet[ModelType]) -> None:
        """Fill pagination metadata (like total count, pages, etc.)."""
        pass


# Concrete implementations


class DisabledPagination(Pagination[ModelType]):
    """Pagination class that disables pagination."""

    @classmethod
    def from_query(cls) -> 'DisabledPagination':
        return cls()

    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        return queryset


class LimitOffsetPagination(Pagination[ModelType]):
    """Limit/Offset based pagination."""

    offset: int = 0
    limit: int = 10
    total: int = 0

    @classmethod
    def from_query(
        cls,
        offset: int = Query(0, ge=0, description='Number of records to skip'),
        limit: int = Query(10, ge=1, le=100, description='Number of records to return'),
    ) -> 'LimitOffsetPagination':
        return cls(offset=offset, limit=limit)

    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        return queryset.offset(self.offset).limit(self.limit)

    async def fill_meta(self, queryset: QuerySet[ModelType]) -> None:
        self.total = await queryset.count()


class PageNumberPagination(Pagination[ModelType]):
    """Page number based pagination."""

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
        return cls(page=page, size=size)

    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        offset = (self.page - 1) * self.size
        return queryset.offset(offset).limit(self.size)

    async def fill_meta(self, queryset: QuerySet[ModelType]) -> None:
        self.total = await queryset.count()
        self.pages = math.ceil(self.total / self.size) if self.size > 0 else 0


class CursorPagination(Pagination[ModelType]):
    """Cursor based pagination."""

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
        return cls(cursor=cursor, size=size)

    def get_cursor_field(self) -> str:
        return self.cursor_field

    def encode_cursor(self, obj: ModelType) -> str:
        field_value = getattr(obj, self.get_cursor_field())
        return str(field_value)

    def decode_cursor(self, cursor_str: str) -> Any:
        if not cursor_str:
            return None

        try:
            # Try to convert to int first (most common case for ID fields)
            return int(cursor_str)
        except (ValueError, TypeError):
            # If not int, return as string
            return cursor_str

    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
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

    async def fill_meta(self, queryset: QuerySet[ModelType]) -> None:
        """Fill cursor metadata."""
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
