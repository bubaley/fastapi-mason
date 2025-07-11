# Routes

Routes are the backbone of how ViewSets translate into actual API endpoints. FastAPI Mason automatically registers routes for your ViewSet methods and handles the complex routing logic behind the scenes.

## How Routes Work

When you decorate a ViewSet with `@viewset(router)`, FastAPI Mason:

1. **Analyzes the ViewSet class** - Identifies which mixins are used (List, Create, Retrieve, etc.)
2. **Registers standard routes** - Creates endpoints for CRUD operations
3. **Registers custom actions** - Adds endpoints for methods decorated with `@action`
4. **Handles route conflicts** - Sorts routes to prevent conflicts between specific and generic patterns
5. **Wraps endpoints** - Adds middleware for permissions, state management, and response formatting

## Standard Routes

Different ViewSet types automatically register different sets of routes:

### ModelViewSet Routes

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
```

This automatically creates:

| HTTP Method | Path | Action | Description |
|-------------|------|--------|-------------|
| `GET` | `/companies/` | `list` | List all companies (paginated) |
| `POST` | `/companies/` | `create` | Create new company |
| `GET` | `/companies/{item_id}/` | `retrieve` | Get specific company |
| `PUT` | `/companies/{item_id}/` | `update` | Update specific company |
| `DELETE` | `/companies/{item_id}/` | `destroy` | Delete specific company |

### ReadOnlyViewSet Routes

```python
@viewset(router)
class CompanyViewSet(ReadOnlyViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
```

This creates only read operations:

| HTTP Method | Path | Action | Description |
|-------------|------|--------|-------------|
| `GET` | `/companies/` | `list` | List all companies (paginated) |
| `GET` | `/companies/{item_id}/` | `retrieve` | Get specific company |

## Action Routes

Custom actions create additional routes based on their configuration:

### Collection Actions (detail=False)

```python
@action(methods=['GET'], detail=False)
async def stats(self):
    return {"total": await Company.all().count()}

@action(methods=['POST'], detail=False, path='bulk-create')
async def bulk_create(self, companies: List[CompanyCreateSchema]):
    # Implementation
    pass
```

Creates:
- `GET /companies/stats/`
- `POST /companies/bulk-create/`

### Instance Actions (detail=True)

```python
@action(methods=['POST'], detail=True)
async def activate(self, item_id: int):
    # Implementation
    pass

@action(methods=['GET'], detail=True, path='detailed-info')
async def detailed_info(self, item_id: int):
    # Implementation
    pass
```

Creates:
- `POST /companies/{item_id}/activate/`
- `GET /companies/{item_id}/detailed-info/`

## Route Priority and Conflicts

FastAPI Mason automatically handles route conflicts by sorting routes based on specificity:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    @action(methods=['GET'], detail=False)
    async def active(self):
        """Get active companies"""
        pass
    
    @action(methods=['GET'], detail=False, path='search')
    async def search(self, query: str):
        """Search companies"""
        pass
```

Route registration order:
1. **Static paths first**: `/companies/active/`, `/companies/search/`
2. **Dynamic paths last**: `/companies/{item_id}/`

This prevents the dynamic `{item_id}` route from capturing requests meant for static actions.

## Route Wrapping

Every route is automatically wrapped with functionality for:

### State Management

Each request gets access to:

```python
def get_queryset(self):
    # Access request context
    user = self.user          # Current user
    request = self.request    # FastAPI Request object
    action = self.action      # Current action name ('list', 'create', etc.)
    
    return Company.all()
```

### Permission Checking

Routes automatically apply permission checks:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    # Permissions are automatically checked for all routes
```

### Response Formatting

Routes apply configured wrappers:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
    
    # All routes automatically use these wrappers
```

## Route Parameters

### Automatic Parameter Injection

ViewSets automatically handle common parameters:

```python
# List endpoint automatically supports pagination
GET /companies/?page=1&size=10

# Actions get parameters from query string, path, or body
@action(methods=['GET'], detail=False)
async def search(self, query: str, limit: int = 10):
    # query and limit come from query parameters
    pass
```

### Custom Path Parameters

```python
@action(methods=['GET'], detail=False, path='by-category/{category}')
async def by_category(self, category: str):
    """Custom path parameter"""
    return await Company.filter(category=category)

# Creates: GET /companies/by-category/{category}/
```

## Behind the Scenes: Route Registration

Here's what happens when you use `@viewset(router)`:

### 1. Mixin Analysis

```python
# FastAPI Mason analyzes your ViewSet inheritance
class CompanyViewSet(ModelViewSet[Company]):
    # ModelViewSet includes: ListMixin, RetrieveMixin, CreateMixin, UpdateMixin, DestroyMixin
    pass
```

### 2. Route Creation

```python
# Each mixin registers its routes
ListMixin.register_routes(viewset_instance, router)
CreateMixin.register_routes(viewset_instance, router)
# ... etc
```

### 3. Action Registration

```python
# @action decorated methods are discovered and registered
for method_name in dir(viewset_class):
    method = getattr(viewset_class, method_name)
    if hasattr(method, '_is_action'):
        register_action_route(viewset_instance, method)
```

### 4. Route Sorting

```python
# Routes are sorted by specificity to prevent conflicts
router.routes = sort_routes_by_specificity(router.routes)
```

## Advanced Route Customization

### Custom Route Configuration

You can customize how routes are generated:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    def get_list_response_model(self):
        """Customize list endpoint response model"""
        if self.list_wrapper:
            return self.list_wrapper[self.many_read_schema, self.pagination]
        return list[self.many_read_schema]
    
    def get_single_response_model(self):
        """Customize single endpoint response model"""
        if self.single_wrapper:
            return self.single_wrapper[self.read_schema]
        return self.read_schema
```

### Conditional Route Registration

Create ViewSets that register different routes based on configuration:

```python
class BaseCompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only register certain actions if user is admin
        if hasattr(self, 'user') and self.user and self.user.is_admin:
            self.register_admin_actions()
    
    def register_admin_actions(self):
        """Register additional actions for admin users"""
        # Custom logic to add admin-only routes
        pass
```

## Route Debugging

### Viewing Registered Routes

You can inspect which routes were registered:

```python
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

# Print all registered routes
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        print(f"{route.methods} {route.path}")
```

### Route Information

Access route information in your ViewSet:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    def get_queryset(self):
        print(f"Current action: {self.action}")
        print(f"Request method: {self.request.method}")
        print(f"Request path: {self.request.url.path}")
        return Company.all()
```

## Examples from the Codebase

### Company ViewSet Routes

```python title="app/domains/company/views.py"
router = APIRouter(prefix='/companies', tags=['companies'])

@viewset(router)
class CompanyViewSet(BaseModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    @action(methods=['GET'], detail=False)
    async def stats(self):
        return 'Hello World!'
```

This creates:
- `GET /companies/` (list)
- `POST /companies/` (create)
- `GET /companies/{item_id}/` (retrieve)
- `PUT /companies/{item_id}/` (update)
- `DELETE /companies/{item_id}/` (destroy)
- `GET /companies/stats/` (custom action)

### Task ViewSet with Custom List

```python title="app/domains/project/views.py"
task_router = APIRouter(prefix='/tasks', tags=['tasks'])

@decorators.viewset(task_router)
class TaskViewSet(ModelViewSet[Task]):
    model = Task
    read_schema = TaskReadSchema
    create_schema = TaskCreateSchema

    @decorators.action(response_model=list[TaskReadSchema])
    async def list(self, project_id: int):
        queryset = Task.filter(project_id=project_id)
        return await TaskReadSchema.from_queryset(queryset)
```

This replaces the standard list route with a custom implementation that requires a `project_id` parameter.

## Best Practices

### 1. Use Descriptive Action Names

```python
# Good: Clear what the action does
@action(methods=['POST'], detail=True)
async def activate(self, item_id: int):
    pass

# Bad: Unclear action name
@action(methods=['POST'], detail=True)
async def do_something(self, item_id: int):
    pass
```

### 2. Group Related Actions

```python
# Group related functionality in the same ViewSet
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    
    @action(methods=['POST'], detail=True)
    async def activate(self, item_id: int):
        pass
    
    @action(methods=['POST'], detail=True)
    async def deactivate(self, item_id: int):
        pass
    
    @action(methods=['GET'], detail=False)
    async def active_companies(self):
        pass
```

### 3. Use Appropriate HTTP Methods

```python
# GET for data retrieval
@action(methods=['GET'], detail=False)
async def stats(self):
    pass

# POST for actions that create or modify
@action(methods=['POST'], detail=True)
async def activate(self, item_id: int):
    pass

# DELETE for removal operations
@action(methods=['DELETE'], detail=False)
async def bulk_delete(self, ids: List[int]):
    pass
```

### 4. Handle Route Conflicts

```python
# Avoid generic patterns that might conflict
# Bad: Too generic
@action(methods=['GET'], detail=False, path='{anything}')
async def generic_handler(self, anything: str):
    pass

# Good: Specific paths
@action(methods=['GET'], detail=False, path='export/{format}')
async def export(self, format: str):
    pass
```

Understanding routes helps you leverage the full power of FastAPI Mason's automatic endpoint generation while maintaining clean, predictable API designs. 