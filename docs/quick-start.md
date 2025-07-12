# Quick Start

Get up and running with FastAPI Mason in just a few minutes! This guide will walk you through installation and building your first API with proper project structure.

## 📦 Installation

Install FastAPI Mason using pip:

```bash
uv add fastapi-mason
```

You'll also need FastAPI and an ORM. FastAPI Mason works great with Tortoise ORM:

```bash
uv add fastapi tortoise-orm
```

## 🏗️ Recommended Project Structure

Before diving into code, **recommend** using a **domains architecture** for your FastAPI projects. This approach organizes your code by business domains rather than technical layers, making it more maintainable and scalable.

Here's the recommended structure:

```
your_project/
├── app/
│   ├── core/                 # Shared utilities and base classes
│   │   ├── models.py         # BaseModel and common fields
│   │   ├── database.py       # Database configuration
│   │   └── settings.py       # Application settings
│   ├── domains/              # Business domains
│   │   └── project/
│   │       ├── models.py     # Business models
│   │       ├── meta.py       # Schema metadata
│   │       ├── schemas.py    # Pydantic schemas
│   │       └── views.py      # API endpoints
│   └── main.py               # FastAPI application setup
```

This structure provides:

- **Clear separation** of business concerns
- **Easy navigation** and understanding
- **Better testability** and maintainability
- **Natural scaling** as your project grows

## ⚙️ Project Setup

Let's build a project management API with related tasks to demonstrate FastAPI Mason's capabilities with linked models.

### 1. Create Base Model

First, create a base model with common fields:

```python title="app/core/models.py"
from tortoise import fields
from tortoise.models import Model

class BaseModel(Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True

BASE_FIELDS = ('id', 'created_at', 'updated_at')
```

### 2. Define Your Models

Create your Tortoise ORM models with ForeignKey relationships:

```python title="app/domains/project/models.py"
from tortoise import fields
from app.core.models import BaseModel

class Project(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    status = fields.CharField(max_length=50, default='active')
    # Reverse relation to tasks will be available as 'tasks' automaticly

class Task(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    completed = fields.BooleanField(default=False)
    project = fields.ForeignKeyField('models.Project', related_name='tasks')
```

### 3. Create Schema Meta Classes

Define which fields to include in your API schemas and how to handle relationships:

```python title="app/domains/project/meta.py"
from app.core.models import BASE_FIELDS
from fastapi_mason.schemas import SchemaMeta, generate_schema_meta

class ProjectMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'description',
        'status',
    )

class TaskMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'description',
        'completed',
        'project_id',  # Include foreign key ID
    )

# Create meta for nested schemas with relationships
def get_project_with_tasks_meta():
    """Project schema with embedded tasks"""
    return generate_schema_meta(
        ProjectMeta,
        ('tasks', get_task_with_project_meta()),
    )

def get_task_with_project_meta():
    """Task schema with embedded project data"""
    return generate_schema_meta(TaskMeta, ('project', ProjectMeta))
```

### 4. Generate Schemas

Use FastAPI Mason's schema generation to create Pydantic models for related data:

```python title="app/domains/project/schemas.py"
from typing import TYPE_CHECKING
from tortoise.contrib.pydantic import PydanticModel

from app.domains.project.meta import (
    ProjectMeta,
    get_project_with_tasks_meta,
    get_task_with_project_meta
)
from app.domains.project.models import Project, Task
from fastapi_mason.schemas import ConfigSchemaMeta, generate_schema, rebuild_schema

# Simple project schema
ProjectReadSchema = generate_schema(Project, meta=ProjectMeta)

# Detailed project schema with tasks (handles circular references)
ProjectDetailSchema = generate_schema(
    Project,
    meta=get_project_with_tasks_meta(),
    config=ConfigSchemaMeta(allow_cycles=True),  # Handle circular references
)

# Create schemas (exclude readonly fields)
ProjectCreateSchema = rebuild_schema(ProjectReadSchema, exclude_readonly=True)

# Task schemas
TaskReadSchema = generate_schema(Task, meta=get_task_with_project_meta())
TaskCreateSchema = rebuild_schema(TaskReadSchema, exclude_readonly=True)

# Type checking support
if TYPE_CHECKING:
    ProjectReadSchema = type('ProjectReadSchema', (Project, PydanticModel), {})
    ProjectCreateSchema = type('ProjectCreateSchema', (Project, PydanticModel), {})
    ProjectDetailSchema = type('ProjectDetailSchema', (Project, PydanticModel), {})
    TaskReadSchema = type('TaskReadSchema', (Task, PydanticModel), {})
    TaskCreateSchema = type('TaskCreateSchema', (Task, PydanticModel), {})
```

### 5. Create Your ViewSets

Now create ViewSets for both models with relationship handling:

```python title="app/domains/project/views.py"
from fastapi import APIRouter
from fastapi_mason.decorators import viewset, action
from fastapi_mason.viewsets import ModelViewSet
from fastapi_mason.pagination import PageNumberPagination
from fastapi_mason.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper

from app.domains.project.models import Project, Task
from app.domains.project.schemas import (
    ProjectReadSchema,
    ProjectDetailSchema,
    ProjectCreateSchema,
    TaskReadSchema,
    TaskCreateSchema
)

router = APIRouter(prefix='/projects', tags=['projects'])

@viewset(router)
class ProjectViewSet(ModelViewSet[Project]):
    model = Project
    read_schema = ProjectReadSchema
    create_schema = ProjectCreateSchema

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper

    def get_queryset(self):
        return Project.all()

    def get_detail_schema(self):
        # Use detailed schema for single item retrieval
        return ProjectDetailSchema

    async def get_object(self, item_id: int):
        # For detail view, also include tasks
        return await Project.get(id=item_id).prefetch_related('tasks')

    @action(methods=['GET'], detail=True)
    async def tasks(self, item_id: int):
        """Get all tasks for a project"""
        project = await self.get_object(item_id)
        tasks = await Task.filter(project=project).select_related('project')
        return [TaskReadSchema.model_validate(task) for task in tasks]

    @action(methods=['POST'], detail=True)
    async def add_task(self, item_id: int, task_data: TaskCreateSchema):
        """Add a new task to the project"""
        project = await self.get_object(item_id)
        task = await Task.create(project=project, **task_data.model_dump())
        await task.fetch_related('project')
        return TaskReadSchema.model_validate(task)

    @action(methods=['POST'], detail=True)
    async def complete(self, item_id: int):
        """Mark project as completed"""
        project = await self.get_object(item_id)
        project.status = 'completed'
        await project.save()
        return {"message": "Project marked as completed"}
```

### 6. Setup FastAPI Application

Wire everything together in your main application:

```python title="app/main.py"
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.domains.project.views import router as projects_router

app = FastAPI(
    title="Project Management API",
    description="A project management API built with FastAPI Mason",
    version="1.0.0"
)

# Register database
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["app.domains.project.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Include ViewSet router
app.include_router(projects_router)
```

### 7. Run Your API

Start the development server:

```bash
uvicorn app.main:app --reload
```

## 🎉 What You Get

Your API is now running at `http://localhost:8000` with these endpoints:

### Project Endpoints

| Method   | Endpoint                   | Description               |
| -------- | -------------------------- | ------------------------- |
| `GET`    | `/projects/`               | List projects (paginated) |
| `POST`   | `/projects/`               | Create new project        |
| `GET`    | `/projects/{item_id}/`          | Get project with tasks    |
| `PUT`    | `/projects/{item_id}/`          | Update project            |
| `DELETE` | `/projects/{item_id}/`          | Delete project            |
| `GET`    | `/projects/{item_id}/tasks/`    | Get all tasks for project |
| `POST`   | `/projects/{item_id}/add_task/` | Add task to project       |
| `POST`   | `/projects/{item_id}/complete/` | Mark project as completed |

## 📋 API Response Examples

### List Projects

```json title="GET /projects/?page=1&size=10"
{
  "data": [
    {
      "id": 1,
      "name": "Website Redesign",
      "description": "Complete overhaul of company website",
      "status": "active",
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
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

### Get Project Details (with tasks)

```json title="GET /projects/1/"
{
  "data": {
    "id": 1,
    "name": "Website Redesign",
    "description": "Complete overhaul of company website",
    "status": "active",
    "tasks": [
      {
        "id": 1,
        "name": "Design mockups",
        "description": "Create UI/UX mockups for the new website",
        "completed": false,
        "project_id": 1,
        "project": {
          "id": 1,
          "name": "Website Redesign",
          "description": "Complete overhaul of company website",
          "status": "active"
        },
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z"
      }
    ],
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

### Create Project

```json title="POST /projects/"
// Request body:
{
  "name": "Mobile App",
  "description": "iOS and Android mobile application",
  "status": "active"
}

// Response:
{
  "data": {
    "id": 2,
    "name": "Mobile App",
    "description": "iOS and Android mobile application",
    "status": "active",
    "created_at": "2024-01-15T13:00:00Z",
    "updated_at": "2024-01-15T13:00:00Z"
  }
}
```

### Add Task to Project

```json title="POST /projects/1/add_task/"
// Request body:
{
  "name": "Setup development environment",
  "description": "Configure development tools and dependencies",
  "completed": false
}

// Response:
{
  "id": 2,
  "name": "Setup development environment",
  "description": "Configure development tools and dependencies",
  "completed": false,
  "project_id": 1,
  "project": {
    "id": 1,
    "name": "Website Redesign",
    "description": "Complete overhaul of company website",
    "status": "active"
  },
  "created_at": "2024-01-15T14:00:00Z",
  "updated_at": "2024-01-15T14:00:00Z"
}
```

## 🔧 Key Features Demonstrated

### 1. **Relationship Handling**

- ForeignKey relationships automatically included in schemas
- Nested object serialization with `generate_schema_meta`
- Circular reference handling with `ConfigSchemaMeta(allow_cycles=True)`

### 2. **Flexible Schema Generation**

- Different schemas for list vs detail views
- Automatic exclusion of readonly fields in create schemas
- Customizable field inclusion through meta classes

### 3. **Optimized Queries**

- `select_related()` for ForeignKey relations
- `prefetch_related()` for reverse relations
- Efficient database queries out of the box

### 4. **Custom Actions**

- Easy addition of custom endpoints with `@action` decorator
- Automatic routing and documentation generation

## 👋 Adding Authentication

Want to add authentication? It's easy with state management:

```python title="app/core/auth.py"
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_mason.state import BaseStateManager
from typing import Optional

class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: Optional[HTTPAuthorizationCredentials] = None
        try:
            credentials = await super().__call__(request)
        except HTTPException:
            # No credentials provided — allow anonymous
            return None
        return credentials

security = OptionalHTTPBearer()

async def get_current_user(token: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if token and token.credentials == "token":  # Your logic
        user = {"id": 1, "username": "john"}
        BaseStateManager.set_user(user)
        return user
    return None
```

Then add it as app dependency or or to the required routers:

```python title="app/main.py"
from app.core.auth import get_current_user

app = FastAPI(
    title="Project Management API",
    description="A project management API built with FastAPI Mason",
    version="1.0.0",
    dependencies=[Depends(get_current_user)]
)
```

## 🛡️ Adding Permissions

Protect your endpoints with permission classes:

```python title="app/domains/project/views.py"
from fastapi_mason.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

@viewset(router)
class ProjectViewSet(ModelViewSet[Project]):
    # ... other configuration ...

    # permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        # Custom permissions per action
        if self.action in ['add_task', 'tasks', 'complete']:
            return [IsAuthenticated()]
        return []
```

## 🎯 Next Steps

Congratulations! You've built a complete REST API with related models using FastAPI Mason. Here's what to explore next:

- **[ViewSets](viewsets/index.md)** - Learn about advanced ViewSet features
- **[Schemas](schemas.md)** - Master schema generation and relationships
- **[Permissions](permissions.md)** - Implement complex authorization rules
- **[Pagination](pagination.md)** - Explore different pagination strategies
- **[State Management](state.md)** - Share data across your application
- **[Response Wrappers](wrappers.md)** - Customize API response formatting

## 💡 Tips

!!! tip "Domains Architecture"
Keep your domains focused and cohesive. Each domain should represent a clear business concept with its own models, schemas, and views.

!!! tip "Relationship Performance"
Always use `select_related()` for ForeignKey fields and `prefetch_related()` for reverse relations to avoid N+1 query problems.

!!! tip "Schema Flexibility"
Use different meta classes for different use cases - simple schemas for lists, detailed schemas for single items, and minimal schemas for creation.

!!! tip "Documentation"
FastAPI automatically generates OpenAPI documentation. Visit `/docs` to see your interactive API documentation with all relationship data!
