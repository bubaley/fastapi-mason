"""
Response wrapper classes for FastAPI+ library.

Provides flexible response formatting and wrapping strategies
for API responses.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from pydantic import BaseModel

from fastapi_mason.pagination import Pagination
from fastapi_mason.types import T

PaginationType = TypeVar('PaginationType', bound=Pagination)


class ResponseWrapper(ABC, BaseModel, Generic[T]):
    """
    Abstract base class for response wrappers.

    Response wrappers are used to format API responses in a consistent way.
    They can add metadata, status information, or structure data in a specific format.
    """

    @classmethod
    @abstractmethod
    def wrap(cls, data: T, *args, **kwargs) -> 'ResponseWrapper':
        """
        Wrap data in the response format.

        Args:
            data: The data to wrap
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Wrapped response
        """
        pass


class PaginatedResponseWrapper(ABC, BaseModel, Generic[T, PaginationType]):
    """
    Abstract base class for paginated response wrappers.

    These wrappers are specifically designed to handle paginated responses
    and include pagination metadata.
    """

    @classmethod
    @abstractmethod
    def wrap(
        cls, data: List[T], pagination: PaginationType | None = None, *args, **kwargs
    ) -> 'PaginatedResponseWrapper':
        """
        Wrap paginated data in the response format.

        Args:
            data: The list of data items
            pagination: Pagination metadata
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Wrapped paginated response
        """
        pass


# Concrete implementations


class ResponseDataWrapper(ResponseWrapper[T]):
    """
    Simple wrapper that puts data in a 'data' field.

    Example:
    {
        "data": {...}
    }
    """

    data: T

    @classmethod
    def wrap(cls, data: T, *args, **kwargs) -> 'ResponseDataWrapper':
        """Wrap data in data field."""
        return cls(data=data)


class StatusResponseWrapper(ResponseWrapper[T]):
    """
    Wrapper that includes status field along with data.

    Example:
    {
        "status": "success",
        "data": {...}
    }
    """

    status: str = 'success'
    data: T

    @classmethod
    def wrap(cls, data: T, status: str = 'success', *args, **kwargs) -> 'StatusResponseWrapper':
        """Wrap data with status field."""
        return cls(data=data, status=status)


class ListDataWrapper(ResponseWrapper[T]):
    """
    Simple wrapper for list data.

    Example:
    {
        "data": [...]
    }
    """

    data: List[T]

    @classmethod
    def wrap(cls, data: List[T], *args, **kwargs) -> 'ListDataWrapper':
        """Wrap list data in data field."""
        return cls(data=data)


class PaginatedResponseDataWrapper(PaginatedResponseWrapper[T, PaginationType]):
    """
    Standard paginated response wrapper.

    Example:
    {
        "data": [...],
        "meta": {
            "page": 1,
            "size": 10,
            "total": 100,
            "pages": 10
        }
    }
    """

    data: List[T]
    meta: PaginationType

    @classmethod
    def wrap(cls, data: List[T], pagination: PaginationType, *args, **kwargs) -> 'PaginatedResponseDataWrapper':
        """Wrap paginated data with metadata."""
        return cls(data=data, meta=pagination)
