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
