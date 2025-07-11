# Pagination

FastAPI Mason provides multiple pagination strategies to efficiently handle large datasets. Each strategy is designed for different use cases and offers various trade-offs between performance, consistency, and user experience.

## Overview

FastAPI Mason supports four pagination strategies:

1. **DisabledPagination** - No pagination (returns all results)
2. **LimitOffsetPagination** - Traditional limit/offset pagination
3. **PageNumberPagination** - Page-based pagination
4. **CursorPagination** - Cursor-based pagination for consistent results

## Pagination in ViewSets

Set pagination on your ViewSet class:

```python
from fastapi_mason.pagination import PageNumberPagination
from fastapi_mason.viewsets import ModelViewSet
from fastapi_mason.wrappers import PaginatedResponseDataWrapper

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    # Configure pagination
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper  # Include pagination metadata
```

## Disabled Pagination

Use when you want to return all results without pagination:

```python
from fastapi_mason.pagination import DisabledPagination

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = DisabledPagination
    list_wrapper = None  # No pagination metadata needed
```

**Response:**
```json
[
  {"id": 1, "name": "Company A"},
  {"id": 2, "name": "Company B"},
  {"id": 3, "name": "Company C"}
]
```

## Page Number Pagination

The most common pagination strategy, using page numbers and page size:

```python
from fastapi_mason.pagination import PageNumberPagination

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = PageNumberPagination  # Default: 10 items per page
```

### Query Parameters

- `page` (int, default=1): Page number to retrieve
- `size` (int, default=10, max=100): Number of items per page

### API Usage

```bash
GET /companies/?page=2&size=5
```

### Response Format

```json
{
  "data": [
    {"id": 6, "name": "Company F"},
    {"id": 7, "name": "Company G"},
    {"id": 8, "name": "Company H"},
    {"id": 9, "name": "Company I"},
    {"id": 10, "name": "Company J"}
  ],
  "meta": {
    "page": 2,
    "size": 5,
    "total": 25,
    "pages": 5
  }
}
```

### Metadata Fields

| Field | Description |
|-------|-------------|
| `page` | Current page number |
| `size` | Number of items per page |
| `total` | Total number of items |
| `pages` | Total number of pages |

## Limit/Offset Pagination

Traditional pagination using offset and limit:

```python
from fastapi_mason.pagination import LimitOffsetPagination

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = LimitOffsetPagination
```

### Query Parameters

- `offset` (int, default=0): Number of items to skip
- `limit` (int, default=10, max=100): Number of items to return

### API Usage

```bash
GET /companies/?offset=10&limit=5
```

### Response Format

```json
{
  "data": [
    {"id": 11, "name": "Company K"},
    {"id": 12, "name": "Company L"},
    {"id": 13, "name": "Company M"},
    {"id": 14, "name": "Company N"},
    {"id": 15, "name": "Company O"}
  ],
  "meta": {
    "offset": 10,
    "limit": 5,
    "total": 25
  }
}
```

## Cursor Pagination

Provides consistent pagination results even when data is being added/removed:

```python
from fastapi_mason.pagination import CursorPagination

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = CursorPagination
```

### Query Parameters

- `cursor` (string, optional): Cursor for the current position
- `size` (int, default=10, max=100): Number of items per page

### API Usage

```bash
# First page
GET /companies/?size=5

# Next page using cursor from previous response
GET /companies/?cursor=eyJpZCI6NX0&size=5
```

### Response Format

```json
{
  "data": [
    {"id": 1, "name": "Company A"},
    {"id": 2, "name": "Company B"},
    {"id": 3, "name": "Company C"},
    {"id": 4, "name": "Company D"},
    {"id": 5, "name": "Company E"}
  ],
  "meta": {
    "cursor": null,
    "size": 5,
    "next_cursor": "eyJpZCI6NX0",
    "previous_cursor": null,
    "has_next": true,
    "has_previous": false
  }
}
```

### Cursor Configuration

Customize cursor behavior:

```python
class CustomCursorPagination(CursorPagination):
    cursor_field = 'created_at'  # Use timestamp instead of ID
    ordering = 'desc'           # Descending order (newest first)

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = CustomCursorPagination
```

## Custom Pagination

Create your own pagination class:

```python
from fastapi_mason.pagination import Pagination
from fastapi import Query
from pydantic import BaseModel

class CustomPagination(Pagination[ModelType]):
    page_size: int = 20
    page_num: int = 1
    total_items: int = 0
    
    @classmethod
    def from_query(
        cls,
        page: int = Query(1, ge=1, description='Page number'),
        per_page: int = Query(20, ge=1, le=50, description='Items per page'),
    ) -> 'CustomPagination':
        return cls(page_num=page, page_size=per_page)
    
    def paginate(self, queryset):
        offset = (self.page_num - 1) * self.page_size
        return queryset.offset(offset).limit(self.page_size)
    
    async def fill_meta(self, queryset):
        self.total_items = await queryset.count()

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = CustomPagination
```

## Pagination in Custom Actions

Use pagination in your custom actions:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = PageNumberPagination
    
    @action(methods=['GET'], detail=False)
    async def active_companies(self):
        """Get paginated list of active companies"""
        queryset = Company.filter(is_active=True)
        pagination = self.pagination.from_query()
        return await self.get_paginated_response(queryset, pagination)
    
    @action(methods=['GET'], detail=False)
    async def search(self, query: str):
        """Search companies with pagination"""
        queryset = Company.filter(name__icontains=query)
        pagination = self.pagination.from_query()
        return await self.get_paginated_response(queryset, pagination)
```

## Conditional Pagination

Apply different pagination based on context:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    def get_pagination(self):
        """Return different pagination based on user role"""
        if self.user and self.user.is_admin:
            return LimitOffsetPagination  # Admins can use offset pagination
        return PageNumberPagination       # Regular users use page pagination
    
    @action(methods=['GET'], detail=False)
    async def list_with_custom_pagination(self):
        pagination_class = self.get_pagination()
        pagination = pagination_class.from_query()
        queryset = self.get_queryset()
        return await self.get_paginated_response(queryset, pagination)
```

## Performance Considerations

### Page Number vs Limit/Offset

**Page Number Pagination:**
- ✅ User-friendly (page 1, 2, 3...)
- ✅ Easy to implement navigation
- ❌ Performance degrades with high page numbers
- ❌ Results can shift when data changes

**Limit/Offset Pagination:**
- ✅ Flexible offset positioning
- ✅ Good for admin interfaces
- ❌ Same performance issues as page pagination
- ❌ Not user-friendly for large datasets

### Cursor Pagination

**Advantages:**
- ✅ Consistent results (no duplicates/missing items)
- ✅ Better performance for large datasets
- ✅ Works well with real-time data

**Disadvantages:**
- ❌ Can't jump to arbitrary pages
- ❌ More complex to implement navigation
- ❌ Requires sortable cursor field

### Database Index Optimization

Ensure proper indexing for pagination fields:

```sql
-- For cursor pagination on created_at
CREATE INDEX idx_company_created_at ON company(created_at);

-- For ID-based pagination
CREATE INDEX idx_company_id ON company(id);

-- For filtered pagination
CREATE INDEX idx_company_active_created ON company(is_active, created_at);
```

## Best Practices

### 1. Choose the Right Pagination

```python
# For user-facing APIs with small datasets
pagination = PageNumberPagination

# For admin interfaces or APIs with flexible access
pagination = LimitOffsetPagination

# For real-time feeds or large datasets
pagination = CursorPagination

# For small, relatively static datasets
pagination = DisabledPagination
```

### 2. Set Reasonable Limits

```python
class SafePageNumberPagination(PageNumberPagination):
    @classmethod
    def from_query(
        cls,
        page: int = Query(1, ge=1, le=1000),  # Max 1000 pages
        size: int = Query(10, ge=1, le=50),   # Max 50 items per page
    ):
        return cls(page=page, size=size)
```

### 3. Use Appropriate Response Wrappers

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = PageNumberPagination
    
    # Use paginated wrapper for lists
    list_wrapper = PaginatedResponseDataWrapper
    
    # Use simple wrapper for single items
    single_wrapper = ResponseDataWrapper
```

### 4. Handle Empty Results

```python
# Pagination automatically handles empty results
{
  "data": [],
  "meta": {
    "page": 1,
    "size": 10,
    "total": 0,
    "pages": 0
  }
}
```

### 5. Document Pagination

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    """
    Company ViewSet with pagination.
    
    Pagination:
    - Default page size: 10 items
    - Maximum page size: 100 items
    - Use ?page=N&size=M for navigation
    """
    pagination = PageNumberPagination
```

## Frontend Integration

### React Example

```javascript
const [companies, setCompanies] = useState([]);
const [pagination, setPagination] = useState({});

const fetchCompanies = async (page = 1, size = 10) => {
  const response = await fetch(`/api/companies/?page=${page}&size=${size}`);
  const data = await response.json();
  
  setCompanies(data.data);
  setPagination(data.meta);
};

// Pagination component
const Pagination = () => (
  <div>
    <button 
      disabled={pagination.page === 1}
      onClick={() => fetchCompanies(pagination.page - 1)}
    >
      Previous
    </button>
    
    <span>Page {pagination.page} of {pagination.pages}</span>
    
    <button 
      disabled={pagination.page === pagination.pages}
      onClick={() => fetchCompanies(pagination.page + 1)}
    >
      Next
    </button>
  </div>
);
```

### Cursor Pagination Frontend

```javascript
const [companies, setCompanies] = useState([]);
const [cursors, setCursors] = useState({ next: null, previous: null });

const fetchCompanies = async (cursor = null, direction = 'next') => {
  const url = cursor 
    ? `/api/companies/?cursor=${cursor}&size=10`
    : '/api/companies/?size=10';
    
  const response = await fetch(url);
  const data = await response.json();
  
  setCompanies(data.data);
  setCursors({
    next: data.meta.next_cursor,
    previous: data.meta.previous_cursor
  });
};
```

## Real-World Examples

### Example 1: Company List with Search

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    
    @action(methods=['GET'], detail=False)
    async def search(
        self, 
        query: str,
        category: Optional[str] = None,
        is_active: bool = True
    ):
        """Search companies with filters and pagination"""
        queryset = Company.filter(is_active=is_active)
        
        if query:
            queryset = queryset.filter(name__icontains=query)
        
        if category:
            queryset = queryset.filter(category=category)
        
        pagination = self.pagination.from_query()
        return await self.get_paginated_response(queryset, pagination)
```

### Example 2: Task List with Cursor Pagination

```python
class TaskCursorPagination(CursorPagination):
    cursor_field = 'created_at'
    ordering = 'desc'  # Newest tasks first

@viewset(task_router)
class TaskViewSet(ModelViewSet[Task]):
    pagination = TaskCursorPagination
    
    @action(methods=['GET'], detail=False)
    async def by_project(self, project_id: int):
        """Get tasks for a project with cursor pagination"""
        queryset = Task.filter(project_id=project_id)
        pagination = self.pagination.from_query()
        return await self.get_paginated_response(queryset, pagination)
```

Pagination in FastAPI Mason provides the flexibility to handle datasets of any size while maintaining good performance and user experience. 