# Permissions

FastAPI Mason provides a robust permission system that allows you to control access to your API endpoints. The system is inspired by Django REST Framework and provides both view-level and object-level permissions.

## Overview

The permission system consists of:

1. **Permission Classes** - Define access rules
2. **Permission Checking** - Automatic verification on each request
3. **Custom Permissions** - Create your own access logic
4. **Object-Level Permissions** - Fine-grained control per object

## Basic Permission Usage

Set permissions on your ViewSet:

```python
from fastapi_mason.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from fastapi_mason.viewsets import ModelViewSet

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    
    # Apply permissions to all actions
    permission_classes = [IsAuthenticatedOrReadOnly]
```

## Built-in Permission Classes

### IsAuthenticated

Allows access only to authenticated users:

```python
from fastapi_mason.permissions import IsAuthenticated

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated]
    
    # All endpoints require authentication
```

### IsAuthenticatedOrReadOnly

Allows read access to everyone, write access only to authenticated users:

```python
from fastapi_mason.permissions import IsAuthenticatedOrReadOnly

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    # GET requests: anyone can access
    # POST/PUT/DELETE: only authenticated users
```

### DenyAll

Denies all access (useful for disabled endpoints):

```python
from fastapi_mason.permissions import DenyAll

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [DenyAll]
    
    # All requests will be denied with 403
```

## Setting Up Authentication

Permissions work with FastAPI Mason's state management. Set up authentication to populate the user:

```python title="auth.py"
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi_mason.state import BaseStateManager

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    """Authenticate user and set state"""
    # Your authentication logic
    user = await authenticate_token(token.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Set user in state for permission checking
    BaseStateManager.set_user(user)
    return user

# Apply to your router
router = APIRouter(
    prefix='/companies',
    tags=['companies'],
    dependencies=[Depends(get_current_user)]  # Authenticate all requests
)
```

## Conditional Permissions

Apply different permissions based on the action:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticatedOrReadOnly]  # Default permissions
    
    def get_permissions(self):
        """Customize permissions per action"""
        if self.action in ('stats', 'public_info'):
            return []  # No permissions required
        
        if self.action == 'sensitive_data':
            return [IsAuthenticated()]  # Require authentication
        
        if self.action in ('create', 'update', 'destroy'):
            return [IsOwnerOrAdmin()]  # Custom permission
        
        return super().get_permissions()  # Use default
```

## Custom Permission Classes

Create your own permission classes by inheriting from `BasePermission`:

### IsOwner Permission

```python
from fastapi_mason.permissions import BasePermission
from fastapi import HTTPException

class IsOwner(BasePermission):
    """Allow access only to object owners"""
    
    async def has_object_permission(self, request, view, obj):
        """Check if user owns the object"""
        if not view.user:
            return False
        
        # Assuming obj has an 'owner' field
        return hasattr(obj, 'owner') and obj.owner == view.user.id

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated, IsOwner]
```

### Role-Based Permission

```python
class HasRole(BasePermission):
    """Check if user has specific role"""
    
    def __init__(self, required_role: str):
        self.required_role = required_role
    
    async def has_permission(self, request, view):
        """Check user role"""
        if not view.user:
            return False
        
        return getattr(view.user, 'role', None) == self.required_role

class IsAdmin(HasRole):
    """Shortcut for admin role"""
    
    def __init__(self):
        super().__init__('admin')

class IsManager(HasRole):
    """Shortcut for manager role"""
    
    def __init__(self):
        super().__init__('manager')

# Usage
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated, IsAdmin]
```

### Organization-Based Permission

```python
class SameOrganization(BasePermission):
    """Allow access only within same organization"""
    
    async def has_object_permission(self, request, view, obj):
        if not view.user:
            return False
        
        user_org = getattr(view.user, 'organization_id', None)
        obj_org = getattr(obj, 'organization_id', None)
        
        return user_org and obj_org and user_org == obj_org

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated, SameOrganization]
```

## Complex Permission Logic

### Multiple Permission Classes

All permission classes must pass:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [
        IsAuthenticated,      # User must be authenticated
        IsOwner,             # AND user must own the object
        IsActive,            # AND user must be active
    ]
```

### Conditional Permission Combinations

```python
class IsOwnerOrAdmin(BasePermission):
    """Allow access to owners or admins"""
    
    async def has_object_permission(self, request, view, obj):
        if not view.user:
            return False
        
        # Check if user is admin
        if getattr(view.user, 'is_admin', False):
            return True
        
        # Check if user is owner
        return hasattr(obj, 'owner') and obj.owner == view.user.id

class IsPublicOrAuthenticated(BasePermission):
    """Allow public objects to anyone, private to authenticated users"""
    
    async def has_object_permission(self, request, view, obj):
        # Public objects are accessible to everyone
        if getattr(obj, 'is_public', False):
            return True
        
        # Private objects require authentication
        return bool(view.user)
```

## Permission Error Handling

Customize error messages:

```python
class CustomPermission(BasePermission):
    PERMISSION_DENIED_MESSAGE = "You don't have permission to access this resource"
    OBJECT_PERMISSION_DENIED_MESSAGE = "You don't have permission to access this specific object"
    
    async def has_permission(self, request, view):
        # Your logic here
        return True
```

## Action-Specific Permissions

### Method-Based Permissions

```python
from fastapi_mason.permissions import SAFE_METHODS

class ReadOnlyUnlessOwner(BasePermission):
    """Read-only for everyone, write access for owners"""
    
    async def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        
        # Write permissions only for owners
        if not view.user:
            return False
        
        return hasattr(obj, 'owner') and obj.owner == view.user.id
```

### Custom Action Permissions

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        # Public stats endpoint
        if self.action == 'stats':
            return []
        
        # Admin-only export
        if self.action == 'export':
            return [IsAuthenticated(), IsAdmin()]
        
        # Owner-only sensitive data
        if self.action == 'financial_data':
            return [IsAuthenticated(), IsOwner()]
        
        return super().get_permissions()
    
    @action(methods=['GET'], detail=False)
    async def stats(self):
        """Public statistics - no permissions needed"""
        return {"total": await Company.all().count()}
    
    @action(methods=['GET'], detail=False)
    async def export(self):
        """Admin-only export"""
        return {"download_url": "/exports/companies.csv"}
    
    @action(methods=['GET'], detail=True)
    async def financial_data(self, item_id: int):
        """Owner-only financial data"""
        company = await self.get_object(item_id)
        return {"revenue": company.revenue, "profit": company.profit}
```

## Permission Examples from Codebase

### Company ViewSet Example

```python title="app/domains/company/views.py"
from fastapi_mason.permissions import IsAuthenticated

@viewset(router)
class CompanyViewSet(BaseModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    def get_queryset(self):
        if not self.user:
            return Company.filter(id__lte=3)  # Limited access for anonymous users
        return Company.all()

    def get_permissions(self):
        if self.action in ('stats', 'list'):
            return []  # Public access for these actions
        return [IsAuthenticated()]  # Require auth for others

    @action(methods=['GET'], detail=False)
    async def stats(self):
        return 'Hello World!'
```

## Best Practices

### 1. Principle of Least Privilege

```python
# Good: Start with restrictive permissions
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated, IsOwner]  # Restrictive by default
    
    def get_permissions(self):
        # Selectively allow public access
        if self.action in ('list', 'public_stats'):
            return []
        return super().get_permissions()
```

### 2. Separate Authentication from Authorization

```python
# Authentication dependency
async def authenticate_user(token: str = Depends(security)):
    user = await get_user_from_token(token)
    BaseStateManager.set_user(user)
    return user

# Authorization in ViewSet
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsOwner]  # Focus on authorization logic
```

### 3. Use Descriptive Permission Names

```python
class CanManageCompany(BasePermission):
    """User can manage companies in their organization"""
    pass

class CanViewFinancials(BasePermission):
    """User can view financial data"""
    pass

# Clear intent
permission_classes = [CanManageCompany, CanViewFinancials]
```

### 4. Test Permission Logic

```python
# Test your permissions thoroughly
async def test_company_permissions():
    # Test authenticated user
    user = create_user(role='user')
    BaseStateManager.set_user(user)
    
    permission = IsOwner()
    company = create_company(owner=user.id)
    
    assert await permission.has_object_permission(request, view, company)
    
    # Test unauthorized user
    other_user = create_user(role='user')
    BaseStateManager.set_user(other_user)
    
    assert not await permission.has_object_permission(request, view, company)
```

### 5. Document Permission Requirements

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    """
    Company management API.
    
    Permissions:
    - List/Retrieve: Public access
    - Create/Update/Delete: Authenticated users only
    - Financial data: Company owners only
    - Export: Admin users only
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
```

## Advanced Patterns

### Permission Composition

```python
class HasAnyRole(BasePermission):
    """Check if user has any of the specified roles"""
    
    def __init__(self, *roles):
        self.roles = roles
    
    async def has_permission(self, request, view):
        if not view.user:
            return False
        
        user_role = getattr(view.user, 'role', None)
        return user_role in self.roles

# Usage
class AdminOrManager(HasAnyRole):
    def __init__(self):
        super().__init__('admin', 'manager')
```

### Time-Based Permissions

```python
from datetime import datetime, time

class BusinessHoursOnly(BasePermission):
    """Allow access only during business hours"""
    
    async def has_permission(self, request, view):
        now = datetime.now().time()
        business_start = time(9, 0)  # 9 AM
        business_end = time(17, 0)   # 5 PM
        
        return business_start <= now <= business_end
```

### Rate-Limited Permissions

```python
class RateLimitedPermission(BasePermission):
    """Implement simple rate limiting"""
    
    def __init__(self, max_requests=100, time_window=3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    async def has_permission(self, request, view):
        if not view.user:
            return False
        
        user_id = view.user.id
        now = datetime.now().timestamp()
        
        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if now - req_time < self.time_window
            ]
        else:
            self.requests[user_id] = []
        
        # Check rate limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[user_id].append(now)
        return True
```

The permission system in FastAPI Mason provides the flexibility to implement any access control pattern while keeping your code clean and testable. 