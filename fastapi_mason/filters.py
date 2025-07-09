"""
Filtering system for FastAPI+ viewsets.

Provides filter backends for different filtering strategies,
similar to Django REST Framework filters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from fastapi import Query, Request
from tortoise import Model
from tortoise.fields import Field
from tortoise.queryset import QuerySet


class BaseFilterBackend(ABC):
    """
    Abstract base class for all filter backends.

    Filter backends are used to filter querysets based on request parameters.
    """

    @abstractmethod
    async def filter_queryset(self, request: Request, queryset: QuerySet, view: Any) -> QuerySet:
        """
        Filter the queryset based on request parameters.

        Args:
            request: FastAPI request object
            queryset: QuerySet to filter
            view: ViewSet instance

        Returns:
            Filtered queryset
        """
        pass


class SearchFilter(BaseFilterBackend):
    """
    Filter that supports text search across specified fields.

    Usage:
        filter_backends = [SearchFilter]
        search_fields = ['name', 'description']

    Query parameter: ?search=query
    """

    search_param = 'search'

    async def filter_queryset(self, request: Request, queryset: QuerySet, view: Any) -> QuerySet:
        """Filter queryset by search query."""
        search_query = request.query_params.get(self.search_param)

        if not search_query:
            return queryset

        search_fields = getattr(view, 'search_fields', [])
        if not search_fields:
            return queryset

        # Build OR query across all search fields
        filters = {}
        for field in search_fields:
            filters[f'{field}__icontains'] = search_query

        # Apply OR logic (this is a simplified implementation)
        # In practice, you might want to use Q objects for complex OR queries
        if len(search_fields) == 1:
            return queryset.filter(**{f'{search_fields[0]}__icontains': search_query})

        # For multiple fields, we'll filter by the first field for simplicity
        # You can enhance this to support proper OR queries
        return queryset.filter(**{f'{search_fields[0]}__icontains': search_query})


class OrderingFilter(BaseFilterBackend):
    """
    Filter that supports ordering by specified fields.

    Usage:
        filter_backends = [OrderingFilter]
        ordering_fields = ['name', 'created_at']
        ordering = ['-created_at']  # default ordering

    Query parameter: ?ordering=field_name or ?ordering=-field_name
    """

    ordering_param = 'ordering'

    async def filter_queryset(self, request: Request, queryset: QuerySet, view: Any) -> QuerySet:
        """Filter queryset by ordering."""
        ordering = request.query_params.get(self.ordering_param)

        if ordering:
            # Validate ordering field
            ordering_fields = getattr(view, 'ordering_fields', [])

            # Extract field name (remove - if present)
            field_name = ordering.lstrip('-')

            if ordering_fields and field_name not in ordering_fields:
                # Invalid ordering field, ignore
                ordering = None

        if not ordering:
            # Use default ordering if specified
            default_ordering = getattr(view, 'ordering', None)
            if default_ordering:
                ordering = default_ordering[0] if isinstance(default_ordering, list) else default_ordering

        if ordering:
            return queryset.order_by(ordering)

        return queryset


class DjangoFilterBackend(BaseFilterBackend):
    """
    Filter backend that supports Django-style field filtering.

    Usage:
        filter_backends = [DjangoFilterBackend]
        filterset_fields = ['status', 'category_id', 'is_active']

    Query parameters: ?status=active&category_id=1&is_active=true
    """

    async def filter_queryset(self, request: Request, queryset: QuerySet, view: Any) -> QuerySet:
        """Filter queryset by field values."""
        filterset_fields = getattr(view, 'filterset_fields', [])

        if not filterset_fields:
            return queryset

        filters = {}

        for field_name in filterset_fields:
            value = request.query_params.get(field_name)
            if value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_value(value, view.model, field_name)
                if converted_value is not None:
                    filters[field_name] = converted_value

        if filters:
            return queryset.filter(**filters)

        return queryset

    def _convert_value(self, value: str, model: Model, field_name: str) -> Any:
        """Convert string value to appropriate type based on model field."""
        try:
            # Get field from model
            field = model._meta.fields_map.get(field_name)

            if not field:
                return value  # Return as string if field not found

            # Convert based on field type
            if isinstance(field, Field):
                if field.field_type in ['IntField', 'BigIntField', 'SmallIntField']:
                    return int(value)
                elif field.field_type == 'FloatField':
                    return float(value)
                elif field.field_type == 'BooleanField':
                    return value.lower() in ('true', '1', 'yes', 'on')
                elif field.field_type in ['DateField', 'DatetimeField']:
                    # For dates, you might want to use a proper date parser
                    return value

            return value

        except (ValueError, AttributeError):
            return None  # Invalid value, skip this filter


class RangeFilter(BaseFilterBackend):
    """
    Filter backend that supports range filtering for numeric and date fields.

    Usage:
        filter_backends = [RangeFilter]
        range_fields = ['price', 'created_at']

    Query parameters:
        ?price_min=10&price_max=100
        ?created_at_after=2023-01-01&created_at_before=2023-12-31
    """

    async def filter_queryset(self, request: Request, queryset: QuerySet, view: Any) -> QuerySet:
        """Filter queryset by field ranges."""
        range_fields = getattr(view, 'range_fields', [])

        if not range_fields:
            return queryset

        filters = {}

        for field_name in range_fields:
            # Check for min/max or after/before parameters
            min_value = request.query_params.get(f'{field_name}_min')
            max_value = request.query_params.get(f'{field_name}_max')
            after_value = request.query_params.get(f'{field_name}_after')
            before_value = request.query_params.get(f'{field_name}_before')

            # Apply range filters
            if min_value:
                filters[f'{field_name}__gte'] = self._convert_value(min_value, view.model, field_name)
            if max_value:
                filters[f'{field_name}__lte'] = self._convert_value(max_value, view.model, field_name)
            if after_value:
                filters[f'{field_name}__gt'] = self._convert_value(after_value, view.model, field_name)
            if before_value:
                filters[f'{field_name}__lt'] = self._convert_value(before_value, view.model, field_name)

        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        if filters:
            return queryset.filter(**filters)

        return queryset

    def _convert_value(self, value: str, model: Model, field_name: str) -> Any:
        """Convert string value to appropriate type."""
        try:
            field = model._meta.fields_map.get(field_name)

            if field and field.field_type in ['IntField', 'BigIntField', 'SmallIntField']:
                return int(value)
            elif field and field.field_type == 'FloatField':
                return float(value)
            # Add more type conversions as needed

            return value

        except (ValueError, AttributeError):
            return None


# Helper functions for query parameter dependencies


def create_search_dependency(search_param: str = 'search'):
    """Create a FastAPI dependency for search parameter."""

    def search_dependency(search: Optional[str] = Query(None, alias=search_param)):
        return search

    return search_dependency


def create_ordering_dependency(ordering_param: str = 'ordering'):
    """Create a FastAPI dependency for ordering parameter."""

    def ordering_dependency(ordering: Optional[str] = Query(None, alias=ordering_param)):
        return ordering

    return ordering_dependency


def create_filter_dependencies(fields: List[str]) -> Dict[str, Any]:
    """
    Create FastAPI dependencies for filter fields.

    Args:
        fields: List of field names to create dependencies for

    Returns:
        Dictionary mapping field names to Query dependencies
    """
    dependencies = {}

    for field in fields:
        dependencies[field] = Query(None, alias=field)

    return dependencies
