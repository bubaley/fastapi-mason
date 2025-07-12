# Actions

> **Important:** Always add custom routes to your ViewSets using the `@action` decorator. This ensures that you have access to the request context via `self`, and all lifecycle hooks and permission checks are properly handled. Defining routes outside of `@action` will break context and hook processing.

Actions allow you to add custom endpoints to your ViewSets beyond the standard CRUD operations. They're perfect for implementing business logic that doesn't fit into the standard create, read, update, delete pattern.

## What are Actions?

Actions are custom methods in your ViewSet that are automatically registered as API endpoints. They're decorated with the `@action` decorator and can handle various HTTP methods, accept parameters, and return custom responses.

## Basic Action Usage

```python
from fastapi_mason.decorators import action

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    @action(methods=['GET'], detail=False, response_model=dict)
    async def stats(self):
        """Get company statistics"""
        total = await Company.all().count()
        active = await Company.filter(is_active=True).count()
        return {
            "total": total,
            "active": active,
            "inactive": total - active
        }
```

This creates a new endpoint: `GET /companies/stats/`

## Action Parameters

The `@action` decorator accepts several parameters to customize the endpoint:

### methods

Specify which HTTP methods the action accepts:

```python
@action(methods=['GET'])  # Default
async def get_data(self):
    return {"data": "example"}

@action(methods=['POST'])
async def process_data(self):
    return {"status": "processed"}

@action(methods=['GET', 'POST'])
async def flexible_endpoint(self):
    if self.request.method == 'GET':
        return {"data": "viewing"}
    else:
        return {"data": "processing"}
```

### detail

Controls whether the action operates on a single instance or the collection:

```python
# Collection action: /companies/stats/
@action(methods=['GET'], detail=False, response_model=int)
async def stats(self):
    return await Company.all().count()

# Instance action: /companies/{item_id}/activate/
@action(methods=['POST'], detail=True, response_model=dict)
async def activate(self, item_id: int):
    company = await self.get_object(item_id)
    company.is_active = True
    await company.save()
    return {"message": "Company activated"}
```

### path

Customize the URL path for the action:

```python
@action(methods=['GET'], detail=False, path='company-statistics', response_model=dict)
async def stats(self):
    return {"total": await Company.all().count()}

# Creates endpoint: /companies/company-statistics/
```

### name

Set a custom name for the action (used internally):

```python
@action(methods=['GET'], detail=False, name='company_stats', response_model=dict)
async def statistics(self):
    return {"total": await Company.all().count()}
```

### response_model

Specify the response model for OpenAPI documentation:

```python
from pydantic import BaseModel

class StatsResponse(BaseModel):
    total: int
    active: int
    inactive: int

@action(methods=['GET'], detail=False, response_model=StatsResponse)
async def stats(self):
    total = await Company.all().count()
    active = await Company.filter(is_active=True).count()
    return StatsResponse(
        total=total,
        active=active,
        inactive=total - active
    )
```

### Additional FastAPI Parameters

You can pass any additional FastAPI route parameters:

```python
@action(
    methods=['POST'], 
    detail=True,
    status_code=202,
    summary="Activate Company",
    description="Activate a company by setting is_active to True",
    tags=["company-management"]
)
async def activate(self, item_id: int):
    company = await self.get_object(item_id)
    company.is_active = True
    await company.save()
    return {"message": "Company activated"}
```

## Action Types

### Collection Actions (detail=False)

These actions operate on the entire collection and don't require an ID:

```python
@action(methods=['GET'], detail=False)
async def search(self, query: str):
    """Search companies by name"""
    companies = await Company.filter(name__icontains=query)
    return await CompanyReadSchema.from_queryset(companies)

@action(methods=['POST'], detail=False)
async def bulk_create(self, companies: List[CompanyCreateSchema]):
    """Create multiple companies at once"""
    created_companies = []
    for company_data in companies:
        company = await Company.create(**company_data.dict())
        created_companies.append(company)
    return await CompanyReadSchema.from_queryset_single(created_companies)

@action(methods=['GET'], detail=False)
async def export(self):
    """Export companies to CSV"""
    companies = await Company.all()
    # Implementation for CSV export
    return {"download_url": "/exports/companies.csv"}
```

### Instance Actions (detail=True)

These actions operate on a specific instance and require an ID:

```python
@action(methods=['POST'], detail=True)
async def activate(self, item_id: int):
    """Activate a specific company"""
    company = await self.get_object(item_id)
    company.is_active = True
    await company.save()
    return {"message": f"Company {company.name} activated"}

@action(methods=['POST'], detail=True)
async def archive(self, item_id: int):
    """Archive a company instead of deleting it"""
    company = await self.get_object(item_id)
    company.is_archived = True
    company.archived_at = datetime.now()
    await company.save()
    return {"message": "Company archived"}

@action(methods=['GET'], detail=True)
async def employees(self, item_id: int):
    """Get employees for a specific company"""
    company = await self.get_object(item_id)
    employees = await Employee.filter(company=company)
    return await EmployeeReadSchema.from_queryset(employees)
```

## Working with Parameters

Actions can accept various types of parameters:

### Query Parameters

```python
@action(methods=['GET'], detail=False)
async def search(
    self, 
    query: str,
    limit: int = 10,
    active_only: bool = False
):
    """Search companies with filters"""
    queryset = Company.filter(name__icontains=query)
    
    if active_only:
        queryset = queryset.filter(is_active=True)
        
    companies = await queryset.limit(limit)
    return await CompanyReadSchema.from_queryset(companies)
```

### Request Body

```python
from pydantic import BaseModel

class BulkActivateRequest(BaseModel):
    company_ids: List[int]
    reason: str

@action(methods=['POST'], detail=False)
async def bulk_activate(self, request: BulkActivateRequest):
    """Activate multiple companies"""
    companies = await Company.filter(id__in=request.company_ids)
    
    for company in companies:
        company.is_active = True
        company.activation_reason = request.reason
        await company.save()
        
    return {"activated": len(companies)}
```

### Path Parameters

```python
@action(methods=['GET'], detail=False, path='by-category/{category}')
async def by_category(self, category: str):
    """Get companies by category"""
    companies = await Company.filter(category=category)
    return await CompanyReadSchema.from_queryset(companies)

# Creates endpoint: /companies/by-category/{category}/
```

## Pagination in Actions

You can use pagination in your custom actions:

```python
@action(methods=['GET'], detail=False)
async def active_companies(self):
    """Get paginated list of active companies"""
    queryset = Company.filter(is_active=True)
    pagination = self.pagination.from_query()
    return await self.get_paginated_response(queryset, pagination)
```

## Permissions in Actions

Actions inherit the ViewSet's permission classes by default, but you can customize them:

```python
from fastapi_mason.permissions import IsAuthenticated

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        # Custom permissions for specific actions
        if self.action == 'sensitive_data':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    @action(methods=['GET'], detail=False)
    async def sensitive_data(self):
        """This action requires authentication"""
        return {"sensitive": "data"}
```

## Response Wrappers in Actions

Actions can use the ViewSet's response wrappers or specify their own:

```python
@action(methods=['GET'], detail=False)
async def stats(self):
    """Uses ViewSet's wrapper configuration"""
    data = {"total": await Company.all().count()}
    
    # If single_wrapper is configured, wrap the response
    if self.single_wrapper:
        return self.single_wrapper.wrap(data)
    
    return data
```

## Real-World Examples

### Example 1: Company Statistics

```python title="Company Statistics Action"
@action(
    methods=['GET'], 
    detail=False,
    response_model=dict,
    summary="Get company statistics"
)
async def stats(self):
    """Get comprehensive company statistics"""
    total = await Company.all().count()
    active = await Company.filter(is_active=True).count()
    by_category = await Company.all().group_by('category').count()
    
    return {
        "total": total,
        "active": active,
        "inactive": total - active,
        "by_category": by_category,
        "created_today": await Company.filter(
            created_at__gte=datetime.now().replace(hour=0, minute=0, second=0)
        ).count()
    }
```

### Example 2: Task List by Project

```python title="Task List Action from Project Example"
@decorators.action(response_model=list[TaskReadSchema])
async def list(self, project_id: int):
    """Get all tasks for a specific project"""
    queryset = Task.filter(project_id=project_id)
    return await TaskReadSchema.from_queryset(queryset)

# Creates endpoint: /tasks/list/?project_id=123
```

### Example 3: Bulk Operations

```python title="Bulk Operations"
class BulkDeleteRequest(BaseModel):
    ids: List[int]
    reason: str

@action(methods=['POST'], detail=False)
async def bulk_delete(self, request: BulkDeleteRequest):
    """Delete multiple companies at once"""
    await self.check_permissions()  # Ensure user has delete permissions
    
    companies = await Company.filter(id__in=request.ids)
    deleted_count = len(companies)
    
    for company in companies:
        await self.perform_destroy(company)
    
    # Log the bulk deletion
    logger.info(f"Bulk deleted {deleted_count} companies: {request.reason}")
    
    return {
        "deleted": deleted_count,
        "reason": request.reason
    }
```

## Best Practices

### 1. Keep Actions Focused

Each action should have a single, clear purpose:

```python
# Good: Specific action
@action(methods=['POST'], detail=True)
async def activate(self, item_id: int):
    company = await self.get_object(item_id)
    company.is_active = True
    await company.save()
    return {"message": "Company activated"}

# Bad: Action doing too many things
@action(methods=['POST'], detail=True)
async def update_status(self, item_id: int, status: str, notify: bool = True):
    # Too many responsibilities
    pass
```

### 2. Use Appropriate HTTP Methods

```python
# GET for retrieving data
@action(methods=['GET'], detail=False)
async def stats(self):
    return {"total": await Company.all().count()}

# POST for actions that change state
@action(methods=['POST'], detail=True)
async def activate(self, item_id: int):
    # Changes company state
    pass

# PUT for updating entire resources
@action(methods=['PUT'], detail=True)
async def update_settings(self, item_id: int, settings: dict):
    # Updates company settings
    pass
```

### 3. Document Your Actions

```python
@action(
    methods=['POST'], 
    detail=True,
    summary="Activate Company",
    description="Activate a company and send notification emails to users",
    response_model=dict
)
async def activate(self, item_id: int):
    """
    Activate a company.
    
    This action:
    - Sets is_active to True
    - Sends notification emails
    - Logs the activation
    """
    # Implementation
    pass
```

### 4. Handle Errors Gracefully

```python
from fastapi import HTTPException

@action(methods=['POST'], detail=True)
async def activate(self, item_id: int):
    company = await self.get_object(item_id)
    
    if company.is_active:
        raise HTTPException(
            status_code=400, 
            detail="Company is already active"
        )
    
    company.is_active = True
    await company.save()
    return {"message": "Company activated"}
```

Actions provide a powerful way to extend your ViewSets with custom business logic while maintaining the clean, declarative style of FastAPI Mason. 