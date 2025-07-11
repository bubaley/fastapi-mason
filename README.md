# FastAPI Mason

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.13+-green.svg)](https://fastapi.tiangolo.com)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Django REST Framework-inspired ViewSets and utilities for FastAPI applications.

## Features

- **ViewSets**: Django-like ViewSets with automatic CRUD operations
- **Decorators**: Simple registration of ViewSets and custom actions
- **Permissions**: Built-in permission system with customizable access control
- **Pagination**: Multiple pagination strategies (Limit/Offset, Page Number, Cursor)
- **Response Wrappers**: Consistent API response formatting
- **State Management**: Request-scoped state management
- **Type Safety**: Full type hints and generic support

## Installation

```bash
pip install fastapi-mason
```

## Quick Start

### 1. Define your model and schemas

```python
from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

class Company(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField()

    class Meta:
        table = "companies"

# Generate schemas
CompanySchema = pydantic_model_creator(Company, name="CompanySchema")
CompanyCreateSchema = pydantic_model_creator(Company, name="CompanyCreateSchema", exclude_readonly=True)
```

### 2. Create a ViewSet

```python
from fastapi import APIRouter
from fastapi_mason import decorators
from fastapi_mason.viewsets import ModelViewSet
from fastapi_mason.permissions import IsAuthenticated

router = APIRouter(prefix="/companies", tags=["companies"])

@decorators.viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    # Optional: Add permissions
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Company.all()

    @decorators.action()
    async def stats(self):
        total = await Company.all().count()
        return {"total_companies": total}
```

### 3. Include in your FastAPI app

```python
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
```

This automatically creates the following endpoints:
- `GET /companies/` - List companies
- `POST /companies/` - Create company
- `GET /companies/{id}/` - Get specific company
- `PUT /companies/{id}/` - Update company
- `DELETE /companies/{id}/` - Delete company
- `GET /companies/stats/` - Custom action

## Core Components

### ViewSets

#### ModelViewSet
Provides full CRUD operations (Create, Read, Update, Delete):

```python
from fastapi_mason.viewsets import ModelViewSet

class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema
```

#### ReadOnlyViewSet
Provides only read operations (List, Retrieve):

```python
from fastapi_mason.viewsets import ReadOnlyViewSet

class CompanyViewSet(ReadOnlyViewSet[Company]):
    model = Company
    read_schema = CompanySchema
```

### Permissions

Built-in permission classes:

```python
from fastapi_mason.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "list":
            return []  # Allow anonymous access to list
        return [IsAuthenticated()]
```

### Pagination

Multiple pagination strategies available:

```python
from fastapi_mason.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination

class CompanyViewSet(ModelViewSet[Company]):
    pagination = PageNumberPagination  # Default: 10 items per page

    # Or disable pagination
    # pagination = DisabledPagination
```

### Custom Actions

Add custom endpoints with the `@action` decorator:

```python
@decorators.action(methods=["POST"], detail=True)
async def activate(self, item_id: int):
    company = await self.get_object(item_id)
    company.is_active = True
    await company.save()
    return {"message": "Company activated"}

@decorators.action(methods=["get"], detail=False, response_model=dict)
async def statistics(self):
    return {
        "total": await Company.all().count(),
        "active": await Company.filter(is_active=True).count()
    }
```

## Advanced Usage

### Custom Permissions

```python
from fastapi_mason.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    async def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return obj.owner_id == view.user.id
```

### Response Wrappers

Customize response format:

```python
from fastapi_mason.wrappers import ResponseWrapper

class CustomResponseWrapper(ResponseWrapper):
    def wrap(self, data, **kwargs):
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

class CompanyViewSet(ModelViewSet[Company]):
    single_wrapper = CustomResponseWrapper
    list_wrapper = CustomResponseWrapper
```

### State Management

Access request state in your ViewSet:

```python

async def auth_dependency():
    user = {'id': 1, 'name': 'John Doe'}  # Your logic for get user
    BaseStateManager.set_user(user)


router = APIRouter(prefix='/companies', dependencies=[Depends(auth_dependency)])

@decorators.viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    def get_queryset(self):
        if self.state.user:
            return Company.filter(owner=self.state.user)
        return Company.filter(is_public=True)
```

## Examples

Check the `/app` directory for complete examples:

- [Company ViewSet](app/domains/company/views.py) - Basic CRUD with permissions
- [Project ViewSet](app/domains/project/views.py) - Custom actions and pagination

## Requirements

- Python 3.12+
- FastAPI 0.115.13+
- Tortoise ORM 0.25.1+

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'fix(generics): Feature message'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- [ ] Enhanced filtering and searching
- [ ] Advanced serialization options
- [ ] More built-in permission classes
- [ ] Comprehensive documentation site
- [ ] Performance optimizations

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/bubaley/fastapi_mason/issues) on GitHub.
