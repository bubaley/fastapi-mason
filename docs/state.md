# State Management

FastAPI Mason provides a request-scoped state management system that allows you to share data across middleware, ViewSets, and other components within a single request lifecycle. This is essential for passing user information, request context, and other data through your application.

## Overview

The state management system uses Python's `contextvars` to maintain request-scoped data that persists throughout the request lifecycle but is isolated between concurrent requests.

Key features:
- **Request-scoped**: Data is isolated per request
- **Thread-safe**: Works correctly with FastAPI's async nature
- **Automatic cleanup**: State is cleared after each request
- **Flexible storage**: Store any type of data

## Basic Usage

### Setting User Information

The most common use case is storing the current user:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from fastapi_mason.state import BaseStateManager

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    """Authenticate user and store in state"""
    user = await authenticate_token(token.credentials)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Store user in request state
    BaseStateManager.set_user(user)
    return user

# Apply to router
router = APIRouter(
    prefix='/companies',
    dependencies=[Depends(get_current_user)]
)
```

### Accessing State in ViewSets

ViewSets automatically have access to the current state:

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
        action = self.action
        
        if user:
            return Company.filter(owner=user.id)
        return Company.filter(is_public=True)
```

## State Properties

The state manager provides several built-in properties:

### user

The current authenticated user:

```python
def get_queryset(self):
    if self.user:
        # User is authenticated
        return Company.filter(owner=self.user.id)
    else:
        # Anonymous user
        return Company.filter(is_public=True)
```

### request

The current FastAPI Request object:

```python
def get_queryset(self):
    # Access request details
    client_ip = self.request.client.host
    user_agent = self.request.headers.get('user-agent')
    
    # Log request details
    logger.info(f"Request from {client_ip}: {user_agent}")
    
    return Company.all()
```

### action

The current ViewSet action being executed:

```python
def get_permissions(self):
    # Different permissions based on action
    if self.action in ('list', 'retrieve'):
        return []  # Public read access
    elif self.action in ('create', 'update'):
        return [IsAuthenticated()]
    elif self.action == 'destroy':
        return [IsAuthenticated(), IsOwner()]
    
    return super().get_permissions()
```

## Custom State Data

Store custom data in the state:

```python
# In middleware or dependency
state = BaseStateManager.get_state()
state.set('organization_id', user.organization_id)
state.set('request_start_time', time.time())
state.set('feature_flags', {'new_ui': True, 'beta_feature': False})

# In ViewSet
def get_queryset(self):
    state = self.state
    
    # Get custom data
    org_id = state.get('organization_id')
    feature_flags = state.get('feature_flags', {})
    
    queryset = Company.filter(organization_id=org_id)
    
    if feature_flags.get('new_filtering'):
        queryset = queryset.filter(is_featured=True)
    
    return queryset
```

## State Management Methods

### Setting Data

```python
state = BaseStateManager.get_state()

# Set individual values
state.set('key', 'value')
state.set('user_preferences', {'theme': 'dark', 'language': 'en'})

# Set user (shortcut)
BaseStateManager.set_user(user)
```

### Getting Data

```python
state = BaseStateManager.get_state()

# Get with default
value = state.get('key', 'default_value')

# Check if key exists
if state.has('user_preferences'):
    prefs = state.get('user_preferences')

# Direct property access
user = state.user
request = state.request
action = state.action
```

### Removing Data

```python
state = BaseStateManager.get_state()

# Remove specific key
state.remove('temporary_data')

# Clear all custom data (keeps request, user, action)
state.clear()
```

## Custom State Manager

Create your own state manager for additional functionality:

```python
from fastapi_mason.state import BaseStateManager
from typing import Optional

class CustomStateManager(BaseStateManager):
    """Custom state manager with additional properties"""
    
    @property
    def organization_id(self) -> Optional[int]:
        """Get current user's organization ID"""
        if self.user:
            return getattr(self.user, 'organization_id', None)
        return None
    
    @property
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        if self.user:
            return getattr(self.user, 'is_admin', False)
        return False
    
    @property
    def permissions(self) -> list:
        """Get cached user permissions"""
        return self.get('cached_permissions', [])
    
    def cache_permissions(self, permissions: list):
        """Cache user permissions for this request"""
        self.set('cached_permissions', permissions)
    
    def log_activity(self, action: str, details: dict = None):
        """Log user activity"""
        activity = {
            'user_id': self.user.id if self.user else None,
            'action': action,
            'details': details or {},
            'timestamp': time.time(),
            'ip_address': self.request.client.host if self.request else None,
        }
        
        activities = self.get('activities', [])
        activities.append(activity)
        self.set('activities', activities)

# Use custom state manager in ViewSets
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    state_class = CustomStateManager  # Use custom state manager
    
    def get_queryset(self):
        # Access custom properties
        org_id = self.state.organization_id
        is_admin = self.state.is_admin
        
        if is_admin:
            return Company.all()
        elif org_id:
            return Company.filter(organization_id=org_id)
        else:
            return Company.filter(is_public=True)
    
    async def perform_create(self, obj):
        # Log activity
        self.state.log_activity('company_created', {
            'company_name': obj.name
        })
        
        return await super().perform_create(obj)
```

## Middleware Integration

Use state management in middleware:

```python
from fastapi import Request
from fastapi_mason.state import BaseStateManager
import time

async def timing_middleware(request: Request, call_next):
    """Middleware to track request timing"""
    start_time = time.time()
    
    # Set timing data in state
    state = BaseStateManager.get_state()
    state.set('request_start_time', start_time)
    
    response = await call_next(request)
    
    # Calculate and log request duration
    duration = time.time() - start_time
    state.set('request_duration', duration)
    
    # Add duration to response headers
    response.headers['X-Request-Duration'] = str(duration)
    
    return response

# Add to FastAPI app
app.middleware("http")(timing_middleware)
```

### Feature Flag Middleware

```python
async def feature_flag_middleware(request: Request, call_next):
    """Middleware to set feature flags based on user"""
    state = BaseStateManager.get_state()
    
    # Default feature flags
    feature_flags = {
        'new_ui': False,
        'beta_features': False,
        'advanced_search': False,
    }
    
    # Get user from state (set by authentication middleware)
    user = state.user
    
    if user:
        # Enable features based on user role
        if getattr(user, 'is_beta_user', False):
            feature_flags['beta_features'] = True
        
        if getattr(user, 'role', '') == 'admin':
            feature_flags.update({
                'new_ui': True,
                'advanced_search': True,
            })
    
    state.set('feature_flags', feature_flags)
    
    response = await call_next(request)
    return response
```

## Dependency Injection with State

Create dependencies that use state:

```python
from fastapi import Depends

def get_organization_id() -> Optional[int]:
    """Dependency to get current organization ID"""
    state = BaseStateManager.get_state()
    if state.user:
        return getattr(state.user, 'organization_id', None)
    return None

def get_feature_flags() -> dict:
    """Dependency to get current feature flags"""
    state = BaseStateManager.get_state()
    return state.get('feature_flags', {})

def require_admin() -> bool:
    """Dependency that requires admin access"""
    state = BaseStateManager.get_state()
    if not state.user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not getattr(state.user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return True

# Use in endpoints
@router.get("/admin-only")
async def admin_endpoint(
    _: bool = Depends(require_admin),
    org_id: int = Depends(get_organization_id),
    features: dict = Depends(get_feature_flags)
):
    return {
        "organization_id": org_id,
        "features": features,
        "message": "Admin access granted"
    }
```

## State in Custom Actions

Use state in ViewSet actions:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    
    @action(methods=['GET'], detail=False)
    async def my_companies(self):
        """Get companies owned by current user"""
        if not self.user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        companies = await Company.filter(owner=self.user.id)
        
        # Log activity
        self.state.set('last_action', 'viewed_my_companies')
        
        return await self.read_schema.from_queryset(companies)
    
    @action(methods=['POST'], detail=False)
    async def bulk_import(self, file: UploadFile):
        """Import companies from file"""
        start_time = time.time()
        
        # Process file upload
        companies_data = await process_csv(file)
        
        created_companies = []
        for company_data in companies_data:
            company = await Company.create(**company_data)
            created_companies.append(company)
        
        # Store import statistics in state
        duration = time.time() - start_time
        self.state.set('import_stats', {
            'imported_count': len(created_companies),
            'duration': duration,
            'file_name': file.filename,
        })
        
        return {
            "imported": len(created_companies),
            "duration": duration
        }
```

## Best Practices

### 1. Use State for Request-Scoped Data Only

```python
# Good: Request-scoped data
state.set('user_permissions', permissions)
state.set('request_start_time', time.time())
state.set('feature_flags', flags)

# Bad: Application-wide data (use app.state instead)
# state.set('database_connection', db)
# state.set('global_config', config)
```

### 2. Provide Default Values

```python
# Good: Always provide defaults
org_id = state.get('organization_id', None)
features = state.get('feature_flags', {})
cache_ttl = state.get('cache_ttl', 300)

# Bad: May raise KeyError
# org_id = state.organization_id
```

### 3. Clear Sensitive Data

```python
# Clear sensitive data after use
async def process_payment(self):
    # Use payment info
    payment_data = self.state.get('payment_data')
    
    try:
        result = await process_payment(payment_data)
    finally:
        # Clear sensitive data
        self.state.remove('payment_data')
        self.state.remove('credit_card_info')
    
    return result
```

### 4. Use Descriptive Keys

```python
# Good: Descriptive keys
state.set('user_organization_id', org_id)
state.set('feature_flags_cache', flags)
state.set('request_correlation_id', uuid4())

# Bad: Generic keys
state.set('id', org_id)
state.set('flags', flags)
state.set('data', some_data)
```

### 5. Document State Usage

```python
class CompanyViewSet(ModelViewSet[Company]):
    """
    Company management ViewSet.
    
    State Usage:
    - user: Current authenticated user
    - organization_id: User's organization
    - feature_flags: Enabled features for this request
    - audit_trail: Actions performed in this request
    """
    
    def get_queryset(self):
        # Implementation using documented state
        pass
```

## Debugging State

### State Inspection

```python
def debug_state_middleware(request: Request, call_next):
    """Middleware to debug state contents"""
    
    async def process():
        state = BaseStateManager.get_state()
        
        # Log state before processing
        logger.debug(f"Request state: {state.__dict__}")
        
        response = await call_next(request)
        
        # Log state after processing
        logger.debug(f"Final state: {state.__dict__}")
        
        return response
    
    return process()
```

### State Validation

```python
def validate_state():
    """Validate expected state contents"""
    state = BaseStateManager.get_state()
    
    # Check required state
    assert state.user is not None, "User should be set"
    assert state.request is not None, "Request should be set"
    
    # Check custom state
    org_id = state.get('organization_id')
    assert org_id is not None, "Organization ID should be set"
```

State management in FastAPI Mason provides a clean way to share request-scoped data across your application while maintaining thread safety and proper isolation between requests. 