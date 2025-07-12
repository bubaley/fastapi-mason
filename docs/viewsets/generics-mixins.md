# Generics & Mixins

Understanding the architecture behind FastAPI Mason's ViewSets will help you create more powerful and customized APIs. The system is built on a flexible combination of generic classes and mixins that provide specific functionality.

## Architecture Overview

FastAPI Mason uses a layered architecture:

```
ModelViewSet / ReadOnlyViewSet
        ↓
    GenericViewSet (core functionality)
        ↓
    Mixins (add specific routes)
```

### GenericViewSet - The Foundation

`GenericViewSet` contains all the core business logic:

- **Model operations** - Creating, reading, updating, deleting
- **Schema handling** - Converting between models and Pydantic schemas
- **Permission checking** - Applying access control
- **State management** - Managing request context
- **Response formatting** - Applying wrappers and pagination

### Mixins - Route Providers

Mixins only add specific routes to the GenericViewSet. They contain no business logic:

- `ListMixin` - Adds `GET /resources/` endpoint
- `RetrieveMixin` - Adds `GET /resources/{item_id}/` endpoint  
- `CreateMixin` - Adds `POST /resources/` endpoint
- `UpdateMixin` - Adds `PUT /resources/{item_id}/` endpoint
- `DestroyMixin` - Adds `DELETE /resources/{item_id}/` endpoint

## The GenericViewSet

The `GenericViewSet` is the heart of the system. It provides all the methods that mixins use:

```python
from fastapi_mason.generics import GenericViewSet

class CustomViewSet(GenericViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    # All the core functionality is available:
    async def get_object(self, item_id: int) -> Company:
        # Get single object with permission check
        pass
    
    def get_queryset(self) -> QuerySet[Company]:
        # Get base queryset
        pass
    
    async def perform_create(self, obj: Company) -> Company:
        # Customize object creation
        pass
    
    async def check_permissions(self, obj=None) -> None:
        # Check permissions
        pass
```

### Key GenericViewSet Methods

#### Data Access

```python
def get_queryset(self) -> QuerySet[ModelType]:
    """Override to customize base queryset"""
    return self.model.all()

async def get_object(self, item_id: int) -> ModelType:
    """Get single object with permission check"""
    queryset = self.get_queryset()
    obj = await queryset.get_or_none(id=item_id)
    if not obj:
        raise HTTPException(status_code=404, detail='Not found')
    await self.check_permissions(obj)
    return obj
```

#### Lifecycle Hooks

```python
async def perform_create(self, obj: ModelType) -> ModelType:
    """Customize object creation"""
    await obj.save()
    return obj

async def perform_update(self, obj: ModelType) -> ModelType:
    """Customize object updates"""
    await obj.save()
    return obj

async def perform_destroy(self, obj: ModelType) -> None:
    """Customize object deletion"""
    await obj.delete()
```

#### Response Formatting

```python
def get_list_response_model(self) -> Any:
    """Get response model for list endpoints"""
    if self.list_wrapper:
        return self.list_wrapper[self.many_read_schema, self.pagination]
    return list[self.many_read_schema]

def get_single_response_model(self) -> Any:
    """Get response model for single endpoints"""
    if self.single_wrapper:
        return self.single_wrapper[self.read_schema]
    return self.read_schema
```

## Understanding Mixins

Each mixin adds a specific route by calling methods on the GenericViewSet:

### ListMixin

```python
class ListMixin:
    def add_list_route(self):
        async def list_endpoint(pagination=Depends(self.pagination.from_query)):
            # Use GenericViewSet methods
            queryset = self.get_queryset()
            
            if not isinstance(pagination, DisabledPagination):
                return await self.get_paginated_response(
                    queryset=queryset, 
                    pagination=pagination
                )
            
            results = await self.many_read_schema.from_queryset(queryset)
            
            if self.list_wrapper:
                return self.list_wrapper.wrap(data=results, pagination=pagination)
            
            return results
        
        # Register the route
        add_wrapped_route(...)
```

### CreateMixin

```python
class CreateMixin:
    def add_create_route(self):
        async def create_endpoint(data: self.create_schema):
            # Convert schema to model
            obj_data = data.model_dump(exclude_unset=True)
            obj = self.model(**obj_data)
            
            # Use GenericViewSet lifecycle hook
            obj = await self.perform_create(obj)
            
            # Convert back to schema
            result = await self.read_schema.from_tortoise_orm(obj)
            
            if self.single_wrapper:
                return self.single_wrapper.wrap(data=result)
            
            return result
        
        # Register the route
        add_wrapped_route(...)
```

## Creating Custom Mixins

You can create your own mixins to add specialized functionality:

### Example: SoftDeleteMixin

```python
from fastapi_mason.routes import add_wrapped_route

class SoftDeleteMixin:
    """Mixin that adds soft delete functionality"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_soft_delete_routes()
    
    def add_soft_delete_routes(self):
        """Add soft delete and restore routes"""
        
        # Soft delete route
        async def soft_delete_endpoint(item_id: int):
            obj = await self.get_object(item_id)
            obj.is_deleted = True
            obj.deleted_at = datetime.now()
            await obj.save()
            return {"message": "Soft deleted"}
        
        add_wrapped_route(
            viewset=self,
            name='soft_delete',
            path='/{item_id}/soft-delete',
            endpoint=soft_delete_endpoint,
            methods=['POST'],
            status_code=200,
        )
        
        # Restore route
        async def restore_endpoint(item_id: int):
            # Skip permission check for deleted objects
            obj = await self.model.get_or_none(id=item_id)
            if not obj:
                raise HTTPException(status_code=404, detail='Not found')
            obj.is_deleted = False
            obj.deleted_at = None
            await obj.save()
            return {"message": "Restored"}
        
        add_wrapped_route(
            viewset=self,
            name='restore',
            path='/{item_id}/restore',
            endpoint=restore_endpoint,
            methods=['POST'],
            status_code=200,
        )

# Use the custom mixin
class CompanyViewSet(GenericViewSet[Company], SoftDeleteMixin):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
```

### Example: BulkOperationsMixin

```python
class BulkOperationsMixin:
    """Mixin that adds bulk operations"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_bulk_routes()
    
    def add_bulk_routes(self):
        # Bulk create
        async def bulk_create_endpoint(items: List[self.create_schema]):
            created_objects = []
            for item_data in items:
                obj_data = item_data.model_dump(exclude_unset=True)
                obj = self.model(**obj_data)
                obj = await self.perform_create(obj)
                created_objects.append(obj)
            
            results = await self.read_schema.from_queryset_single(created_objects)
            return results
        
        add_wrapped_route(
            viewset=self,
            name='bulk_create',
            path='/bulk',
            endpoint=bulk_create_endpoint,
            methods=['POST'],
            response_model=List[self.read_schema],
            status_code=201,
        )
        
        # Bulk delete
        async def bulk_delete_endpoint(ids: List[int]):
            objects = await self.get_queryset().filter(id__in=ids)
            deleted_count = 0
            
            for obj in objects:
                await self.check_permissions(obj)
                await self.perform_destroy(obj)
                deleted_count += 1
            
            return {"deleted": deleted_count}
        
        add_wrapped_route(
            viewset=self,
            name='bulk_delete',
            path='/bulk',
            endpoint=bulk_delete_endpoint,
            methods=['DELETE'],
            status_code=200,
        )
```

## Custom ViewSet Classes

You can combine GenericViewSet with your own mixin combinations:

### ReadWriteViewSet

```python
from fastapi_mason.generics import GenericViewSet
from fastapi_mason.mixins import ListMixin, RetrieveMixin, CreateMixin, UpdateMixin

class ReadWriteViewSet(
    GenericViewSet[ModelType],
    ListMixin,
    RetrieveMixin, 
    CreateMixin,
    UpdateMixin,
    # Note: No DestroyMixin - no delete functionality
):
    """ViewSet with CRUD except delete"""
    pass
```

### AdminViewSet

```python
class AdminViewSet(
    GenericViewSet[ModelType],
    ListMixin,
    RetrieveMixin,
    CreateMixin,
    UpdateMixin,
    DestroyMixin,
    SoftDeleteMixin,
    BulkOperationsMixin,
):
    """Full-featured admin ViewSet"""
    
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        # Show all objects including soft deleted for admins
        return self.model.all()
```

## Route Registration Process

Understanding how routes are registered helps with debugging and customization:

### 1. Initialization Order

```python
# When you create a ViewSet instance:
class CompanyViewSet(ModelViewSet[Company]):
    # 1. GenericViewSet.__init__() runs
    # 2. Each mixin's __init__() runs, adding routes
    # 3. Action methods are discovered and registered
    # 4. Routes are sorted by specificity
```

### 2. Route Wrapping

Every route goes through the same wrapper pipeline:

```python
async def wrapped_endpoint(*args, **kwargs):
    # 1. Set request state
    state.request = get_request(*args, **kwargs)
    state.action = action_name
    
    # 2. Check permissions
    await viewset.check_permissions()
    
    # 3. Call original endpoint
    try:
        return await original_endpoint(*args, **kwargs)
    finally:
        # 4. Clean up state
        state._clear_state()
```

### 3. Route Conflicts

Routes are sorted to prevent conflicts:

```python
def sort_routes_by_specificity(routes):
    # Static paths (e.g., /companies/stats/) come first
    # Dynamic paths (e.g., /companies/{item_id}/) come last
    # This prevents conflicts between custom actions and CRUD operations
```

## Advanced Customization

### Custom GenericViewSet

You can subclass GenericViewSet to add organization-wide functionality:

```python
class BaseViewSet(GenericViewSet[ModelType]):
    """Custom base ViewSet with common functionality"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add common setup
    
    async def check_permissions(self, obj=None):
        """Add organization-wide permission logic"""
        await super().check_permissions(obj)
        
        # Additional permission checks
        if self.user and not self.user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled")
    
    def get_queryset(self):
        """Add organization-wide filtering"""
        queryset = super().get_queryset()
        
        # Filter by organization
        if hasattr(self.model, 'organization_id') and self.user:
            queryset = queryset.filter(organization_id=self.user.organization_id)
        
        return queryset
```

### Custom Route Registration

For complex route requirements, you can manually register routes:

```python
from fastapi_mason.routes import add_wrapped_route

class CustomViewSet(GenericViewSet[Company]):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_custom_routes()
    
    def add_custom_routes(self):
        async def complex_endpoint(
            param1: str,
            param2: int = 10,
            request_body: Optional[dict] = None
        ):
            # Complex business logic
            pass
        
        add_wrapped_route(
            viewset=self,
            name='complex_operation',
            path='/complex/{param1}',
            endpoint=complex_endpoint,
            methods=['POST', 'PUT'],
            response_model=dict,
            summary="Complex Operation",
            description="Performs complex business logic",
        )
```

## Best Practices

### 1. Separate Concerns

```python
# Good: Mixins only add routes
class ExportMixin:
    def add_export_route(self):
        # Just adds the route
        pass

# Good: Business logic in GenericViewSet methods
class CompanyViewSet(GenericViewSet[Company], ExportMixin):
    async def generate_export(self):
        # Business logic here
        pass
```

### 2. Use Composition Over Inheritance

```python
# Good: Combine mixins for specific functionality
class ReadOnlyWithExportViewSet(
    GenericViewSet[ModelType],
    ListMixin,
    RetrieveMixin,
    ExportMixin,
):
    pass

# Better: Create reusable combinations
class PublicAPIViewSet(ReadOnlyWithExportViewSet):
    permission_classes = []  # Public access
```

### 3. Override Carefully

```python
# When overriding GenericViewSet methods, call super()
class CustomViewSet(ModelViewSet[Company]):
    async def perform_create(self, obj):
        # Add custom logic
        obj.created_by = self.user
        
        # Call original implementation
        return await super().perform_create(obj)
```

The generic and mixin architecture gives you incredible flexibility to build exactly the API you need while maintaining clean, reusable code. 