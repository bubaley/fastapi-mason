# Response Wrappers

Response wrappers in FastAPI Mason provide a consistent way to format API responses. They allow you to wrap your data in a standard structure, add metadata, handle pagination information, and create uniform response formats across your entire API.

## Overview

FastAPI Mason provides two types of response wrappers:

1. **ResponseWrapper** - For single objects and simple responses
2. **PaginatedResponseWrapper** - For paginated list responses with metadata

## Basic Response Wrappers

### ResponseDataWrapper

The most basic wrapper that puts data in a 'data' field:

```python
from fastapi_mason.wrappers import ResponseDataWrapper

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema

    # Wrap single object responses
    single_wrapper = ResponseDataWrapper
```

**Response format:**
```json
{
  "data": {
    "id": 1,
    "name": "Acme Corp",
    "description": "A great company"
  }
}
```

### PaginatedResponseDataWrapper

For paginated list responses with metadata:

```python
from fastapi_mason.wrappers import PaginatedResponseDataWrapper
from fastapi_mason.pagination import PageNumberPagination

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema

    # Wrap list response
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
```

**Response format:**
```json
{
  "data": [
    {"id": 1, "name": "Company A"},
    {"id": 2, "name": "Company B"}
  ],
  "meta": {
    "page": 1,
    "size": 10,
    "total": 25,
    "pages": 3
  }
}
```

## Custom Response Wrappers

### Custom Wrapper

Create your own wrapper for consistent API responses:

```python
from fastapi_mason.wrappers import ResponseWrapper
from datetime import datetime
from fastapi_mason.types import T


class ApiResponseWrapper(ResponseWrapper[T]):
    """Standard API response format"""

    success: bool
    # data: T
    custom_data: T
    timestamp: str

    @classmethod
    def wrap(cls, data: T, **kwargs) -> "ApiResponseWrapper":
        return cls(
            success=True,
            custom_data=data,
            timestamp=datetime.now().isoformat(),
        )
```

**Response format:**
```json
{
  "success": true,
  "custom_data": {
    "id": 1,
    "name": "Acme Corp"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Custom Paginated Wrapper

Create a wrapper with additional metadata:

```python
from fastapi_mason.wrappers import PaginatedResponseWrapper
from fastapi_mason.pagination import PageNumberPagination
from typing import List
from fastapi_mason.types import T


class CustomPaginatedWrapper(PaginatedResponseWrapper[T, PageNumberPagination]):
    """Enhanced paginated response"""

    items: List[T]
    # data: List[T]
    total: int

    @classmethod
    def wrap(cls, data: List[T], pagination: PageNumberPagination, **kwargs) -> "CustomPaginatedWrapper":
        return cls(
            items=data,
            total=pagination.total,
        )
```

**Response format:**
```json
{
  "items": [
    {"id": 1, "name": "Company A"},
    {"id": 2, "name": "Company B"}
  ],
  "total": 2
}
```
