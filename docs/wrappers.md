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
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
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

### Simple Custom Wrapper

Create your own wrapper for consistent API responses:

```python
from fastapi_mason.wrappers import ResponseWrapper
from datetime import datetime
from typing import TypeVar, Generic

T = TypeVar('T')

class ApiResponseWrapper(ResponseWrapper[T]):
    """Standard API response format"""
    
    success: bool
    data: T
    timestamp: str
    
    @classmethod
    def wrap(cls, data: T, **kwargs) -> 'ApiResponseWrapper':
        return cls(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )

# Usage in ViewSet
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    single_wrapper = ApiResponseWrapper
```

**Response format:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Acme Corp"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error-Aware Wrapper

Handle both success and error responses:

```python
from typing import Optional, Any

class StandardResponseWrapper(ResponseWrapper[T]):
    """Response wrapper with error handling"""
    
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    code: Optional[str] = None
    timestamp: str
    
    @classmethod
    def wrap(cls, data: T = None, error: str = None, code: str = None, **kwargs) -> 'StandardResponseWrapper':
        return cls(
            success=error is None,
            data=data if error is None else None,
            error=error,
            code=code,
            timestamp=datetime.now().isoformat()
        )
    
    @classmethod
    def success_response(cls, data: T) -> 'StandardResponseWrapper':
        return cls.wrap(data=data)
    
    @classmethod
    def error_response(cls, error: str, code: str = None) -> 'StandardResponseWrapper':
        return cls.wrap(error=error, code=code)
```

## Paginated Response Wrappers

### Custom Paginated Wrapper

Create a wrapper with additional metadata:

```python
from fastapi_mason.wrappers import PaginatedResponseWrapper
from fastapi_mason.pagination import Pagination
from typing import List, TypeVar

T = TypeVar('T')
P = TypeVar('P', bound=Pagination)

class EnhancedPaginatedWrapper(PaginatedResponseWrapper[T, P]):
    """Enhanced paginated response with additional metadata"""
    
    data: List[T]
    pagination: P
    meta: dict
    
    @classmethod
    def wrap(cls, data: List[T], pagination: P, **kwargs) -> 'EnhancedPaginatedWrapper':
        # Calculate additional metadata
        has_next = hasattr(pagination, 'page') and hasattr(pagination, 'pages') and pagination.page < pagination.pages
        has_prev = hasattr(pagination, 'page') and pagination.page > 1
        
        meta = {
            'pagination': pagination.dict(),
            'count': len(data),
            'has_next': has_next,
            'has_previous': has_prev,
            'timestamp': datetime.now().isoformat(),
        }
        
        return cls(
            data=data,
            pagination=pagination,
            meta=meta
        )
```

### API Standard Wrapper

Industry-standard API response format:

```python
class JsonApiWrapper(PaginatedResponseWrapper[T, P]):
    """JSON:API compliant response wrapper"""
    
    data: List[T]
    links: dict
    meta: dict
    
    @classmethod
    def wrap(cls, data: List[T], pagination: P, request_url: str = "", **kwargs) -> 'JsonApiWrapper':
        # Build pagination links
        links = {"self": request_url}
        
        if hasattr(pagination, 'page') and hasattr(pagination, 'pages'):
            base_url = request_url.split('?')[0]
            
            if pagination.page > 1:
                links["prev"] = f"{base_url}?page={pagination.page - 1}&size={pagination.size}"
            
            if pagination.page < pagination.pages:
                links["next"] = f"{base_url}?page={pagination.page + 1}&size={pagination.size}"
            
            links["first"] = f"{base_url}?page=1&size={pagination.size}"
            links["last"] = f"{base_url}?page={pagination.pages}&size={pagination.size}"
        
        # Build metadata
        meta = {
            "total": getattr(pagination, 'total', 0),
            "page": getattr(pagination, 'page', 1),
            "per_page": getattr(pagination, 'size', len(data)),
            "pages": getattr(pagination, 'pages', 1),
        }
        
        return cls(
            data=data,
            links=links,
            meta=meta
        )
```

## Conditional Wrappers

Apply different wrappers based on context:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    
    def get_single_wrapper(self):
        """Choose wrapper based on user preferences"""
        if self.user and getattr(self.user, 'prefers_verbose_response', False):
            return VerboseResponseWrapper
        return SimpleResponseWrapper
    
    def get_list_wrapper(self):
        """Choose wrapper based on action"""
        if self.action == 'export':
            return ExportResponseWrapper
        return StandardPaginatedWrapper
    
    async def retrieve(self, item_id: int):
        """Override to use dynamic wrapper"""
        obj = await self.get_object(item_id)
        result = await self.read_schema.from_tortoise_orm(obj)
        
        wrapper = self.get_single_wrapper()
        if wrapper:
            return wrapper.wrap(data=result)
        
        return result
```

## Wrapper Configuration

### ViewSet-Level Configuration

Set different wrappers for different response types:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    # Different wrappers for different endpoints
    list_wrapper = PaginatedResponseDataWrapper    # For list endpoint
    single_wrapper = ResponseDataWrapper          # For single object endpoints
    
    # Pagination configuration
    pagination = PageNumberPagination
```

### Action-Specific Wrappers

Use different wrappers for custom actions:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    
    @action(methods=['GET'], detail=False)
    async def stats(self):
        """Custom action with custom wrapper"""
        stats_data = {
            "total": await Company.all().count(),
            "active": await Company.filter(is_active=True).count(),
        }
        
        # Use custom wrapper for this action
        return StatsResponseWrapper.wrap(
            data=stats_data,
            generated_at=datetime.now().isoformat()
        )
    
    @action(methods=['GET'], detail=False)
    async def export(self):
        """Export action with file download wrapper"""
        export_url = await generate_export()
        
        return FileDownloadWrapper.wrap(
            download_url=export_url,
            filename="companies_export.csv",
            expires_at=datetime.now() + timedelta(hours=1)
        )
```

## Advanced Wrapper Features

### Wrapper with Request Context

Access request information in wrappers:

```python
class ContextAwareWrapper(ResponseWrapper[T]):
    """Wrapper that includes request context"""
    
    data: T
    context: dict
    
    @classmethod
    def wrap(cls, data: T, request=None, user=None, **kwargs) -> 'ContextAwareWrapper':
        context = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user.id if user else None,
            "request_id": getattr(request, 'state', {}).get('request_id'),
            "client_ip": request.client.host if request else None,
        }
        
        return cls(data=data, context=context)

# Usage in ViewSet
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    single_wrapper = ContextAwareWrapper
    
    async def retrieve(self, item_id: int):
        obj = await self.get_object(item_id)
        result = await self.read_schema.from_tortoise_orm(obj)
        
        return self.single_wrapper.wrap(
            data=result,
            request=self.request,
            user=self.user
        )
```

### Nested Wrapper System

Create hierarchical wrapper structure:

```python
class NestedDataWrapper(ResponseWrapper[T]):
    """Wrapper with nested structure"""
    
    result: dict
    
    @classmethod
    def wrap(cls, data: T, operation: str = "read", **kwargs) -> 'NestedDataWrapper':
        result = {
            "operation": operation,
            "payload": {
                "data": data,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                }
            },
            "status": {
                "code": 200,
                "message": "success"
            }
        }
        
        return cls(result=result)
```

## Response Wrapper Examples from Codebase

### Base ViewSet Example

```python title="app/core/viewsets.py"
from fastapi_mason.pagination import PageNumberPagination
from fastapi_mason.viewsets import ModelViewSet
from fastapi_mason.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper

class BaseModelViewSet(ModelViewSet[ModelType]):
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
```

### Project ViewSet with Disabled Wrappers

```python title="app/domains/project/views.py"
@decorators.viewset(task_router)
class TaskViewSet(ModelViewSet[Task]):
    model = Task
    read_schema = TaskReadSchema
    create_schema = TaskCreateSchema

    pagination = DisabledPagination
    list_wrapper = None      # No wrapper for list responses
    single_wrapper = None    # No wrapper for single responses
```

## Best Practices

### 1. Consistent Response Format

Use the same wrapper across your API:

```python
# Good: Consistent across all ViewSets
class BaseViewSet(ModelViewSet[ModelType]):
    single_wrapper = ApiResponseWrapper
    list_wrapper = ApiPaginatedWrapper

class CompanyViewSet(BaseViewSet[Company]):
    # Inherits consistent wrappers
    pass

class ProjectViewSet(BaseViewSet[Project]):
    # Same consistent format
    pass
```

### 2. Document Response Format

```python
class ApiResponseWrapper(ResponseWrapper[T]):
    """
    Standard API response wrapper.
    
    Response format:
    {
        "success": true,
        "data": <response_data>,
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """
    
    success: bool
    data: T
    timestamp: str
```

### 3. Handle Edge Cases

```python
class SafeResponseWrapper(ResponseWrapper[T]):
    """Wrapper that handles None data gracefully"""
    
    @classmethod
    def wrap(cls, data: T = None, **kwargs) -> 'SafeResponseWrapper':
        if data is None:
            data = {}  # or appropriate default
        
        return cls(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
```

### 4. Version Your Wrappers

```python
class ApiV1ResponseWrapper(ResponseWrapper[T]):
    """API v1 response format"""
    data: T
    timestamp: str

class ApiV2ResponseWrapper(ResponseWrapper[T]):
    """API v2 response format with additional metadata"""
    data: T
    meta: dict
    timestamp: str

# Use appropriate wrapper based on API version
def get_wrapper_for_version(version: str):
    if version == "v1":
        return ApiV1ResponseWrapper
    return ApiV2ResponseWrapper
```

### 5. Test Your Wrappers

```python
def test_response_wrapper():
    """Test wrapper functionality"""
    data = {"id": 1, "name": "Test"}
    
    response = ApiResponseWrapper.wrap(data)
    
    assert response.success is True
    assert response.data == data
    assert response.timestamp is not None
    
    # Test serialization
    json_response = response.dict()
    assert "success" in json_response
    assert "data" in json_response
    assert "timestamp" in json_response
```

## Common Patterns

### Status Code Wrapper

```python
class StatusResponseWrapper(ResponseWrapper[T]):
    """Wrapper that includes HTTP status information"""
    
    status_code: int
    status_text: str
    data: T
    
    @classmethod
    def wrap(cls, data: T, status_code: int = 200, **kwargs) -> 'StatusResponseWrapper':
        status_text = {
            200: "OK",
            201: "Created",
            204: "No Content",
            400: "Bad Request",
            404: "Not Found",
        }.get(status_code, "Unknown")
        
        return cls(
            status_code=status_code,
            status_text=status_text,
            data=data
        )
```

### Metric Wrapper

```python
class MetricResponseWrapper(ResponseWrapper[T]):
    """Wrapper that includes performance metrics"""
    
    data: T
    metrics: dict
    
    @classmethod
    def wrap(cls, data: T, start_time: float = None, **kwargs) -> 'MetricResponseWrapper':
        end_time = time.time()
        duration = end_time - (start_time or end_time)
        
        metrics = {
            "response_time_ms": round(duration * 1000, 2),
            "data_size": len(str(data)) if data else 0,
            "timestamp": datetime.now().isoformat(),
        }
        
        return cls(data=data, metrics=metrics)
```

Response wrappers in FastAPI Mason provide the flexibility to create consistent, well-structured API responses while maintaining clean separation between your business logic and response formatting. 