# ViewSets

ViewSets are the heart of FastAPI Mason. They provide a Django REST Framework-like approach to building REST APIs with automatic CRUD operations, custom actions, and flexible configuration.

## What are ViewSets?

A ViewSet is a class-based view that groups related actions for a specific resource. Instead of writing separate functions for each HTTP operation, you define a single ViewSet class that handles all operations for your model.

## Basic ViewSet Structure

```python
from fastapi import APIRouter
from fastapi_mason.decorators import viewset
from fastapi_mason.viewsets import ModelViewSet

router = APIRouter(prefix='/companies', tags=['companies'])

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company                     # The Tortoise ORM model to use for this ViewSet
    read_schema = CompanyReadSchema     # Pydantic schema for serializing response data (read operations)
    create_schema = CompanyCreateSchema # Pydantic schema for validating and deserializing input data (create/update)
    
    # Optional configurations
    pagination = PageNumberPagination   # Pagination class to use for list endpoints (default: DisabledPagination)
    permission_classes = [IsAuthenticatedOrReadOnly] # List of permission classes for access control
    list_wrapper = PaginatedResponseDataWrapper      # Wrapper class for formatting paginated list responses
    single_wrapper = ResponseDataWrapper            # Wrapper class for formatting single object responses
```

## ViewSet Types

FastAPI Mason provides two main ViewSet types:

### ModelViewSet

Provides full CRUD operations:

- **List** (`GET /resources/`) - Get paginated list of resources
- **Create** (`POST /resources/`) - Create new resource
- **Retrieve** (`GET /resources/{item_id}/`) - Get specific resource
- **Update** (`PUT /resources/{item_id}/`) - Update resource
- **Destroy** (`DELETE /resources/{item_id}/`) - Delete resource

```python
from fastapi_mason.viewsets import ModelViewSet

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
```

### ReadOnlyViewSet

Provides only read operations:

- **List** (`GET /resources/`) - Get paginated list of resources  
- **Retrieve** (`GET /resources/{item_id}/`) - Get specific resource

```python
from fastapi_mason.viewsets import ReadOnlyViewSet

@viewset(router)
class CompanyViewSet(ReadOnlyViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
```

## ViewSet Configuration

### Required Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `model` | `Type[Model]` | The Tortoise ORM model class associated with this ViewSet. |
| `read_schema` | `Type[PydanticModel]` | Pydantic schema used for serializing response data (read operations). |

### Optional Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `create_schema` | `Type[PydanticModel]` | `None` | Pydantic schema for validating and deserializing input data when creating resources. |
| `update_schema` | `Type[PydanticModel]` | `create_schema` | Pydantic schema for validating and deserializing input data when updating resources. Defaults to `create_schema` if not set. |
| `many_read_schema` | `Type[PydanticModel]` | `read_schema` | Pydantic schema for serializing list responses. Defaults to `read_schema`. |
| `pagination` | `Type[Pagination]` | `DisabledPagination` | Pagination strategy class for list endpoints. |
| `permission_classes` | `List[Type[BasePermission]]` | `[]` | List of permission classes for access control. |
| `list_wrapper` | `Type[ResponseWrapper]` | `None` | Wrapper class for formatting paginated list responses. |
| `single_wrapper` | `Type[ResponseWrapper]` | `None` | Wrapper class for formatting single object responses. |

## Schema Configuration

ViewSets use different schemas for different operations:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    
    # For reading data (GET operations)
    read_schema = CompanyReadSchema
    many_read_schema = CompanyListSchema  # Optional, defaults to read_schema
    
    # For writing data (POST/PUT operations) 
    create_schema = CompanyCreateSchema
    update_schema = CompanyUpdateSchema  # Optional, defaults to create_schema
```

!!! tip "Schema Fallbacks"
    FastAPI Mason provides sensible fallbacks:
    
    - `update_schema` defaults to `create_schema`
    - `create_schema` defaults to `update_schema`  
    - `many_read_schema` defaults to `read_schema`

## Customizing Queries

Override the `get_queryset()` method to customize the base queryset:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    def get_queryset(self):
        # Filter based on user authentication
        if not self.user:
            return Company.filter(is_public=True)
        
        # Show user's own companies and public ones
        return Company.filter(
            Q(owner=self.user) | Q(is_public=True)
        )
```

## Accessing Request Context

ViewSets provide easy access to request context:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    def get_queryset(self):
        # Access current user
        user = self.user
        
        # Access current request
        request = self.request
        
        # Access current action
        action = self.action  # 'list', 'create', 'retrieve', etc.
        
        return Company.all()
```

## Lifecycle Hooks

Customize object creation, updating, and deletion:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    async def perform_create(self, obj: Company) -> Company:
        """Called before saving a new object"""
        obj.owner = self.user
        obj.created_by = self.user.username
        await obj.save()
        return obj
    
    async def perform_update(self, obj: Company) -> Company:
        """Called before saving an updated object"""
        obj.updated_by = self.user.username
        await obj.save()
        return obj
    
    async def perform_destroy(self, obj: Company) -> None:
        """Called before deleting an object"""
        # Soft delete instead of hard delete
        obj.is_deleted = True
        await obj.save()
        # Or use hard delete:
        # await obj.delete()
```

## Examples from the Codebase

Let's look at real examples from the project:

### Company ViewSet

```python title="app/domains/company/views.py"
from fastapi import APIRouter
from app.core.viewsets import BaseModelViewSet
from app.domains.company.models import Company
from app.domains.company.schemas import CompanyCreateSchema, CompanySchema
from fastapi_mason.decorators import action, viewset
from fastapi_mason.permissions import IsAuthenticated

router = APIRouter(prefix='/companies', tags=['companies'])

@viewset(router)
class CompanyViewSet(BaseModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    def get_queryset(self):
        if not self.user:
            return Company.filter(id__lte=3)
        return Company.all()

    def get_permissions(self):
        if self.action in ('stats', 'list'):
            return []
        return [IsAuthenticated()]

    @action(methods=['GET'], detail=False)
    async def stats(self):
        return 'Hello World!'
```

### Project ViewSet with Custom Configuration

```python title="app/domains/project/views.py"
from fastapi import APIRouter
from app.core.viewsets import BaseModelViewSet
from app.domains.project.models import Project, Task
from app.domains.project.schemas import (
    ProjectCreateSchema,
    ProjectReadSchema,
    TaskCreateSchema,
    TaskReadSchema,
)
from fastapi_mason import decorators
from fastapi_mason.pagination import DisabledPagination
from fastapi_mason.viewsets import ModelViewSet

router = APIRouter(prefix='/projects', tags=['projects'])

@decorators.viewset(router)
class ProjectViewSet(BaseModelViewSet[Project]):
    model = Project
    read_schema = ProjectReadSchema
    create_schema = ProjectCreateSchema

# Task ViewSet with disabled pagination and wrappers
task_router = APIRouter(prefix='/tasks', tags=['tasks'])

@decorators.viewset(task_router)
class TaskViewSet(ModelViewSet[Task]):
    model = Task
    read_schema = TaskReadSchema
    create_schema = TaskCreateSchema

    pagination = DisabledPagination
    list_wrapper = None
    single_wrapper = None

    @decorators.action(response_model=list[TaskReadSchema])
    async def list(self, project_id: int):
        queryset = Task.filter(project_id=project_id)
        return await TaskReadSchema.from_queryset(queryset)
```

## Next Steps

Now that you understand the basics of ViewSets, explore these advanced topics:

- **[Actions](actions.md)** - Add custom endpoints to your ViewSets
- **[Routes](routes.md)** - Understand how ViewSets register routes and handle requests
- **[Generics & Mixins](generics-mixins.md)** - Learn about the underlying architecture 