# Quick Start

Get up and running with FastAPI Mason in just a few minutes! This guide will walk you through installation and building your first API.

## 📦 Installation

Install FastAPI Mason using pip:

```bash
pip install fastapi-mason
```

You'll also need FastAPI and an ORM. FastAPI Mason works great with Tortoise ORM:

```bash
pip install fastapi tortoise-orm
```

## 🏗️ Project Setup

Let's build a simple blog API to demonstrate FastAPI Mason's capabilities.

### 1. Define Your Model

Create your Tortoise ORM model:

```python title="models.py"
from tortoise.models import Model
from tortoise import fields

class Post(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    published = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "posts"
```

### 2. Create Schema Meta

Define which fields to include in your API schemas:

```python title="meta.py"
from fastapi_mason.schemas import SchemaMeta

class PostMeta(SchemaMeta):
    include = (
        'id',
        'title', 
        'content',
        'published',
        'created_at',
        'updated_at',
    )
```

### 3. Generate Schemas

Use FastAPI Mason's schema generation to create Pydantic models:

```python title="schemas.py"
from models import Post
from meta import PostMeta
from fastapi_mason.schemas import generate_schema, rebuild_schema

# Generate read schema (includes all fields)
PostReadSchema = generate_schema(Post, meta=PostMeta)

# Generate create schema (excludes readonly fields like id, timestamps)
PostCreateSchema = rebuild_schema(PostReadSchema, exclude_readonly=True)
```

### 4. Create Your ViewSet

Now for the magic - create a complete REST API with just a few lines:

```python title="views.py"
from fastapi import APIRouter
from fastapi_mason.decorators import viewset, action
from fastapi_mason.viewsets import ModelViewSet
from fastapi_mason.pagination import PageNumberPagination
from fastapi_mason.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper

from models import Post
from schemas import PostReadSchema, PostCreateSchema

router = APIRouter(prefix='/posts', tags=['posts'])

@viewset(router)
class PostViewSet(ModelViewSet[Post]):
    model = Post
    read_schema = PostReadSchema
    create_schema = PostCreateSchema
    
    # Enable pagination
    pagination = PageNumberPagination
    
    # Wrap responses in consistent format
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
    
    def get_queryset(self):
        # Only show published posts to unauthenticated users
        if not self.user:
            return Post.filter(published=True)
        return Post.all()
    
    @action(methods=['POST'], detail=True)
    async def publish(self, item_id: int):
        """Custom action to publish a post"""
        post = await self.get_object(item_id)
        post.published = True
        await post.save()
        return {"message": "Post published successfully"}
    
    @action(methods=['GET'], detail=False)
    async def published(self):
        """Get only published posts"""
        queryset = Post.filter(published=True)
        pagination = self.pagination.from_query()
        return await self.get_paginated_response(queryset, pagination)
```

### 5. Setup FastAPI Application

Wire everything together in your main application:

```python title="main.py"
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from views import router as posts_router

app = FastAPI(
    title="Blog API",
    description="A simple blog API built with FastAPI Mason",
    version="1.0.0"
)

# Register database
register_tortoise(
    app,
    db_url="sqlite://./blog.db",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Include ViewSet router
app.include_router(posts_router)
```

### 6. Run Your API

Start the development server:

```bash
uvicorn main:app --reload
```

## 🎉 What You Get

Your API is now running at `http://localhost:8000` with these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/posts/` | List posts (paginated) |
| `POST` | `/posts/` | Create new post |
| `GET` | `/posts/{id}/` | Get specific post |
| `PUT` | `/posts/{id}/` | Update post |
| `DELETE` | `/posts/{id}/` | Delete post |
| `POST` | `/posts/{id}/publish/` | Publish post (custom action) |
| `GET` | `/posts/published/` | Get published posts (custom action) |

## 📋 API Response Examples

### List Posts (with pagination)

```json title="GET /posts/?page=1&size=10"
{
  "data": [
    {
      "id": 1,
      "title": "My First Post", 
      "content": "Hello, world!",
      "published": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "size": 10,
    "total": 1,
    "pages": 1
  }
}
```

### Create Post

```json title="POST /posts/"
// Request body:
{
  "title": "New Post",
  "content": "This is a new post",
  "published": false
}

// Response:
{
  "data": {
    "id": 2,
    "title": "New Post",
    "content": "This is a new post", 
    "published": false,
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

## 🔧 Adding Authentication

Want to add authentication? It's easy with state management:

```python title="auth.py"
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi_mason.state import BaseStateManager

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    # Your authentication logic here
    if token.credentials == "valid-token":
        user = {"id": 1, "username": "john"}
        BaseStateManager.set_user(user)
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )
```

Then add it to your router:

```python title="views.py"
from auth import get_current_user

router = APIRouter(
    prefix='/posts', 
    tags=['posts'],
    dependencies=[Depends(get_current_user)]  # Add authentication
)
```

## 🛡️ Adding Permissions

Protect your endpoints with permission classes:

```python title="views.py"
from fastapi_mason.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

@viewset(router)
class PostViewSet(ModelViewSet[Post]):
    # ... other configuration ...
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        # Custom permissions per action
        if self.action == 'publish':
            return [IsAuthenticated()]
        return super().get_permissions()
```

## 🎯 Next Steps

Congratulations! You've built a complete REST API with FastAPI Mason. Here's what to explore next:

- **[ViewSets](viewsets/index.md)** - Learn about advanced ViewSet features
- **[Schemas](schemas.md)** - Master schema generation and relationships  
- **[Permissions](permissions.md)** - Implement complex authorization rules
- **[Pagination](pagination.md)** - Explore different pagination strategies
- **[State Management](state.md)** - Share data across your application
- **[Response Wrappers](wrappers.md)** - Customize API response formatting

## 💡 Tips

!!! tip "Performance"
    For production, consider using async database drivers and enabling query optimization in Tortoise ORM.

!!! tip "Validation"
    Add custom validation to your schemas using Pydantic validators for business logic.

!!! tip "Documentation"
    FastAPI automatically generates OpenAPI documentation. Visit `/docs` to see your interactive API documentation! 