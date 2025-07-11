# FastAPI Mason 🔨

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.13+-green.svg)](https://fastapi.tiangolo.com)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/bubaley/fastapi-mason/blob/main/LICENSE)

**Django REST Framework-inspired ViewSets and utilities for FastAPI applications.**

FastAPI Mason brings the beloved patterns and conventions from Django REST Framework to FastAPI, providing a structured and efficient way to build REST APIs. With familiar concepts like ViewSets, permissions, pagination, and serialization, you can rapidly develop robust API applications.

Just like skilled masons who craft solid foundations with precision and expertise, FastAPI Mason helps you build reliable, well-structured APIs with time-tested patterns and best practices.

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
Multiple pagination strategies out of the box: Limit/Offset, Page Number, and Cursor pagination.
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

<div class="feature-card">
<h3>🛡️ Type Safety</h3>
Full type hints and generic support for better IDE experience and runtime safety.
</div>

## 🚀 Quick Example

Here's how easy it is to create a complete REST API with FastAPI Mason:

```python
from fastapi import APIRouter
from fastapi_mason.decorators import viewset, action
from fastapi_mason.viewsets import ModelViewSet
from fastapi_mason.pagination import PageNumberPagination
from fastapi_mason.permissions import IsAuthenticatedOrReadOnly

router = APIRouter(prefix='/companies', tags=['companies'])

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema
    
    pagination = PageNumberPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(methods=['GET'], detail=False)
    async def stats(self):
        return {"total": await Company.all().count()}
```

This automatically creates:

- `GET /companies/` - List companies with pagination
- `POST /companies/` - Create new company  
- `GET /companies/{id}/` - Get specific company
- `PUT /companies/{id}/` - Update company
- `DELETE /companies/{id}/` - Delete company
- `GET /companies/stats/` - Custom stats endpoint

## 🎯 Philosophy

FastAPI Mason is designed with these principles in mind:

- **Familiar**: If you know Django REST Framework, you already know FastAPI Mason
- **Flexible**: Customize every aspect while maintaining sensible defaults
- **Fast**: Built on FastAPI's high-performance foundation
- **Type-Safe**: Leverage Python's type system for better development experience
- **Modular**: Use only what you need, when you need it

## 📚 Getting Started

Ready to build amazing APIs? Start with our [Quick Start guide](quick-start.md) to get up and running in minutes.

Want to dive deeper? Explore our comprehensive guides:

- [ViewSets](viewsets/index.md) - Learn about the core ViewSet concepts
- [Schemas](schemas.md) - Master schema generation and meta classes  
- [Permissions](permissions.md) - Secure your APIs with permission classes
- [Pagination](pagination.md) - Implement efficient data pagination
- [State Management](state.md) - Manage request-scoped state
- [Response Wrappers](wrappers.md) - Format consistent API responses

## 🤝 Community

FastAPI Mason is open source and welcomes contributions! Whether you're reporting bugs, suggesting features, or submitting pull requests, your involvement helps make the library better for everyone.

- **GitHub**: [github.com/bubaley/fastapi_mason](https://github.com/bubaley/fastapi-mason)
- **Issues**: Report bugs and request features
- **Discussions**: Get help and share ideas

## 📄 License

FastAPI Mason is released under the [MIT License](https://github.com/bubaley/fastapi-mason/blob/main/LICENSE). 