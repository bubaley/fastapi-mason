# FastAPI Mason

<p align="center">
  <img align="center" src="docs/assets/logo.png" alt="logo" width="200"/>
  <h1 align="center">FastAPI Mason</h1>
</p>
<p align="center" markdown=1>
  <i>Build REST APIs with Django REST Framework patterns in FastAPI</i>
</p>
<p align="center" markdown=1>
<a href="https://pypi.org/project/fastapi-mason/">
  <img src="https://img.shields.io/pypi/v/fastapi-mason?color=%2334D058&label=pypi%20package" alt="PyPi Version"/>
</a>
<a href="https://pypi.org/project/fastapi-mason/">
  <img src="https://img.shields.io/pypi/pyversions/fastapi-mason.svg?color=%2334D058" alt="Supported Python Versions"/>
</a>
<a href="https://github.com/bubaley/fastapi-mason/blob/main/LICENSE">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"/>
</a>
</p>

<hr>

**Transform your FastAPI development with familiar Django REST Framework patterns.**

FastAPI Mason brings the beloved patterns and conventions from Django REST Framework to FastAPI, providing a structured and efficient way to build REST APIs. With familiar concepts like ViewSets, permissions, pagination, and serialization, you can rapidly develop robust API applications.

Just like skilled masons who craft solid foundations with precision and expertise, FastAPI Mason helps you build reliable, well-structured APIs with time-tested patterns and best practices.

<hr>
<p><b>Documentation</b>: <a class="link" href="https://bubaley.github.io/fastapi-mason">bubaley.github.io/fastapi-mason</a></p>
<hr>

<div style="margin: 2rem 0;">
  <a href="https://bubaley.github.io/fastapi-mason/quick-start/" class="get-started-btn">
    Get Started
  </a>
</div>

## 📦 Installation

Install FastAPI Mason using UV:

```bash
uv add fastapi-mason
```

## 🚀 Quick Example

Here's a complete example showing how to build a REST API with FastAPI Mason:

```python
# main.py - Complete FastAPI Mason application
from fastapi import APIRouter, FastAPI
from tortoise import fields
from tortoise.contrib.fastapi import register_tortoise
from tortoise.models import Model

from fastapi_mason.decorators import action, viewset
from fastapi_mason.pagination import PageNumberPagination
from fastapi_mason.schemas import SchemaMeta, build_schema, rebuild_schema
from fastapi_mason.viewsets import ModelViewSet
from fastapi_mason.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper

# Database setup
def register_database(app: FastAPI):
    register_tortoise(
        app,
        db_url='sqlite://db.sqlite3',
        modules={'models': ['main']},
        generate_schemas=True,
        add_exception_handlers=True,
    )

# Models
class Company(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    full_name = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

# Schema meta
class CompanyMeta(SchemaMeta):
    include = ('id', 'name', 'full_name', 'created_at', 'updated_at')

# Schemas
CompanySchema = build_schema(Company, meta=CompanyMeta)
CompanyCreateSchema = rebuild_schema(CompanySchema, exclude_readonly=True)

# Views
router = APIRouter(prefix='/companies', tags=['companies'])

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper

    # permission_classes = [IsAuthenticatedOrReadOnly]

    @action(methods=['GET'], detail=False, response_model=dict[str, int])
    async def stats(self):
        return {'total': await Company.all().count()}

# Application
app = FastAPI(title='My API')
register_database(app)
app.include_router(router)
```

Start server:

```bash
uvicorn main:app --reload
```

 Try API Endpoints:

```python
"""
This creates the following endpoints:
- GET /companies/ - List companies with pagination
- POST /companies/ - Create new company
- GET /companies/{item_id}/ - Get specific company
- PUT /companies/{item_id}/ - Update company
- DELETE /companies/{item_id}/ - Delete company
- GET /companies/stats/ - Custom stats endpoint

Example API Responses:

GET /companies/ (with pagination wrapper):
{
  "data": [
    {
      "id": 1,
      "name": "Acme Corp",
      "full_name": "Acme Corporation Ltd.",
      "created_at": "2023-01-01T10:00:00Z",
      "updated_at": "2023-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 5,
    "total_items": 47
  }
}

GET /companies/1/ (with single wrapper):
{
  "data": {
    "id": 1,
    "name": "Acme Corp",
    "full_name": "Acme Corporation Ltd.",
    "created_at": "2023-01-01T10:00:00Z",
    "updated_at": "2023-01-01T10:00:00Z"
  }
}

GET /companies/stats/ (custom action):
{
  "total": 123
}
"""
```

## ✨ Key Features

<div class="feature-card">
  <h3>🎯 ViewSets</h3>
Django-like ViewSets with automatic CRUD operations and custom actions. Build complete REST APIs with minimal boilerplate code.
</div>

<div class="feature-card">
<h3>🔒 Permissions</h3>
Built-in permission system with customizable access control. Protect your endpoints with authentication and authorization rules.
</div>

<div class="feature-card">
<h3>📄 Pagination</h3>
Multiple pagination strategies out of the box: Limit/Offset and Page Number. You can easily customize or override pagination classes to suit your needs.
</div>

<div class="feature-card">
<h3>📋 Schema Generation</h3>
Intelligent schema generation with meta classes for fine-grained control over API serialization.
</div>

<div class="feature-card">
<h3>🔄 Response Wrappers</h3>
Consistent API response formatting with customizable wrapper classes.
</div>

<div class="feature-card">
<h3>⚡ State Management</h3>
Request-scoped state management for sharing data across middleware and view components.
</div>

## 🎯 Philosophy

FastAPI Mason is designed with these principles in mind:

- **Familiar**: If you know Django REST Framework, you already know FastAPI Mason
- **Flexible**: Customize every aspect while maintaining sensible defaults
- **Fast**: Built on FastAPI's high-performance foundation
- **Modular**: Use only what you need, when you need it

## 📚 Getting Started

Ready to build amazing APIs? Start with our [Quick Start guide](https://bubaley.github.io/fastapi-mason/quick-start/) to get up and running in minutes.

Want to dive deeper? Explore our comprehensive guides:

- [ViewSets](https://bubaley.github.io/fastapi-mason/viewsets/) - Learn about the core ViewSet concepts
- [Schemas & Meta](https://bubaley.github.io/fastapi-mason/schemas/) - Master schema generation and meta classes
- [Permissions](https://bubaley.github.io/fastapi-mason/permissions/) - Secure your APIs with permission classes
- [Pagination](https://bubaley.github.io/fastapi-mason/pagination/) - Implement efficient data pagination
- [State Management](https://bubaley.github.io/fastapi-mason/state/) - Manage request-scoped state
- [Response Wrappers](https://bubaley.github.io/fastapi-mason/wrappers/) - Format consistent API responses

## 🤝 Community

FastAPI Mason is open source and welcomes contributions! Whether you're reporting bugs, suggesting features, or submitting pull requests, your involvement helps make the library better for everyone.

- **GitHub**: [github.com/bubaley/fastapi-mason](https://github.com/bubaley/fastapi-mason)
- **Issues**: Report bugs and request features
- **Discussions**: Get help and share ideas

## 📄 License

FastAPI Mason is released under the [MIT License](https://github.com/bubaley/fastapi-mason/blob/main/LICENSE).
