# Schemas

FastAPI Mason provides a powerful schema generation system that makes it easy to create Pydantic models from your Tortoise ORM models. The system uses meta classes to give you fine-grained control over which fields are included, excluded, or marked as optional.

## Overview

The schema system consists of three main components:

1. **SchemaMeta** - Defines which fields to include/exclude
2. **generate_schema()** - Creates Pydantic models from Tortoise models
3. **rebuild_schema()** - Modifies existing schemas for different use cases

## SchemaMeta Classes

SchemaMeta classes define the field configuration for your schemas:

```python
from fastapi_mason.schemas import SchemaMeta

class CompanyMeta(SchemaMeta):
    include = (
        'id',
        'name',
        'description',
        'created_at',
        'updated_at',
    )
    exclude = ('internal_notes',)
    optional = ('description',)
    computed = ('full_name',)
```

### SchemaMeta Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `include` | `Tuple[str, ...]` | Fields to include in the schema |
| `exclude` | `Tuple[str, ...]` | Fields to exclude from the schema |
| `optional` | `Tuple[str, ...]` | Fields that should be optional |
| `computed` | `Tuple[str, ...]` | Computed/derived fields |

## Basic Schema Generation

### Simple Schema

```python title="models.py"
from tortoise.models import Model
from tortoise import fields

class Company(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
```

```python title="meta.py"
from fastapi_mason.schemas import SchemaMeta

class CompanyMeta(SchemaMeta):
    include = (
        'id',
        'name',
        'description',
        'is_active',
        'created_at',
        'updated_at',
    )
```

```python title="schemas.py"
from fastapi_mason.schemas import generate_schema, rebuild_schema
from models import Company
from meta import CompanyMeta

# Generate read schema (includes all fields)
CompanyReadSchema = generate_schema(Company, meta=CompanyMeta)

# Generate create schema (excludes readonly fields)
CompanyCreateSchema = rebuild_schema(
    CompanyReadSchema, 
    exclude_readonly=True
)
```

## Advanced Schema Generation

### Using Base Fields

Create reusable base field sets:

```python title="app/core/models.py"
BASE_FIELDS = ('id', 'created_at', 'updated_at')
```

```python title="meta.py"
from app.core.models import BASE_FIELDS
from fastapi_mason.schemas import SchemaMeta

class CompanyMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,  # Include common fields
        'name',
        'description',
        'is_active',
    )
```

### Handling Relationships

Define meta classes for related models:

```python title="models.py"
class Company(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

class Project(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    company = fields.ForeignKeyField('models.Company', related_name='projects')

class Task(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    project = fields.ForeignKeyField('models.Project', related_name='tasks')
```

```python title="meta.py"
from fastapi_mason.schemas import SchemaMeta, generate_schema_meta

class CompanyMeta(SchemaMeta):
    include = ('id', 'name', 'description')

class ProjectMeta(SchemaMeta):
    include = ('id', 'name', 'description', 'company_id')

class TaskMeta(SchemaMeta):
    include = ('id', 'name', 'project_id')

# Generate composite meta for complex relationships
def get_project_with_tasks_meta():
    return generate_schema_meta(
        ProjectMeta,
        ('company', CompanyMeta),     # Include company data
        ('tasks', TaskMeta),          # Include related tasks
    )

def get_task_with_project_meta():
    return generate_schema_meta(
        TaskMeta,
        ('project', ProjectMeta),     # Include project data
    )
```

```python title="schemas.py"
from fastapi_mason.schemas import generate_schema, rebuild_schema, ConfigSchemaMeta
from models import Project, Task
from meta import get_project_with_tasks_meta, get_task_with_project_meta

# Schema with relationships
ProjectReadSchema = generate_schema(
    Project,
    meta=get_project_with_tasks_meta(),
    config=ConfigSchemaMeta(allow_cycles=True),  # Allow circular references
)

TaskReadSchema = generate_schema(
    Task, 
    meta=get_task_with_project_meta()
)

# Create schemas
ProjectCreateSchema = rebuild_schema(ProjectReadSchema, exclude_readonly=True)
TaskCreateSchema = rebuild_schema(TaskReadSchema, exclude_readonly=True)
```

## Schema Rebuilding

The `rebuild_schema()` function allows you to create variations of existing schemas:

### Exclude Readonly Fields

```python
# Original schema includes all fields
UserReadSchema = generate_schema(User, meta=UserMeta)

# Create schema excludes id, created_at, updated_at
UserCreateSchema = rebuild_schema(
    UserReadSchema, 
    exclude_readonly=True
)
```

### Custom Field Selection

```python
# Create a minimal schema with only essential fields
UserMinimalSchema = rebuild_schema(
    UserReadSchema,
    meta=MinimalUserMeta,  # Different meta class
    name="UserMinimalSchema"
)

# Create public schema without sensitive fields
UserPublicSchema = rebuild_schema(
    UserReadSchema,
    meta=PublicUserMeta,
    name="UserPublicSchema"
)
```

## Real-World Examples

### Company Domain Example

```python title="app/domains/company/models.py"
from tortoise import fields
from app.core.models import BaseModel

class Company(BaseModel):  # BaseModel includes id, created_at, updated_at
    name = fields.CharField(max_length=255)
    full_name = fields.TextField(null=True)
```

```python title="app/domains/company/meta.py"
from app.core.models import BASE_FIELDS
from fastapi_mason.schemas import SchemaMeta

class CompanyMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'full_name',
    )
```

```python title="app/domains/company/schemas.py"
from app.domains.company.meta import CompanyMeta
from app.domains.company.models import Company
from fastapi_mason.schemas import generate_schema, rebuild_schema

CompanySchema = generate_schema(Company, meta=CompanyMeta)
CompanyCreateSchema = rebuild_schema(CompanySchema, exclude_readonly=True)
```

### Project Domain with Relationships

```python title="app/domains/project/models.py"
from tortoise import fields
from app.core.models import BaseModel

class Project(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    tasks = fields.ReverseRelation['Task']
    company = fields.ForeignKeyField('models.Company', related_name='projects')

class Task(BaseModel):
    name = fields.CharField(max_length=255)
    project = fields.ForeignKeyField('models.Project', related_name='tasks')
```

```python title="app/domains/project/meta.py"
from app.core.models import BASE_FIELDS
from app.domains.company.meta import CompanyMeta
from fastapi_mason.schemas import SchemaMeta, generate_schema_meta

class ProjectMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'description',
        'company_id',
    )

class TaskMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'project_id',
    )

def get_project_with_tasks_meta():
    return generate_schema_meta(
        ProjectMeta,
        ('company', CompanyMeta),
        ('tasks', get_task_with_project_meta()),
    )

def get_task_with_project_meta():
    return generate_schema_meta(TaskMeta, ('project', ProjectMeta))
```

```python title="app/domains/project/schemas.py"
from typing import TYPE_CHECKING
from tortoise.contrib.pydantic import PydanticModel
from app.domains.project.meta import get_project_with_tasks_meta, get_task_with_project_meta
from app.domains.project.models import Project, Task
from fastapi_mason.schemas import ConfigSchemaMeta, generate_schema, rebuild_schema

ProjectReadSchema = generate_schema(
    Project,
    meta=get_project_with_tasks_meta(),
    config=ConfigSchemaMeta(allow_cycles=True),
)

ProjectCreateSchema = rebuild_schema(
    ProjectReadSchema,
    exclude_readonly=True,
)

TaskReadSchema = generate_schema(Task, meta=get_task_with_project_meta())
TaskCreateSchema = rebuild_schema(TaskReadSchema, exclude_readonly=True)

# Type checking for IDE support
if TYPE_CHECKING:
    ProjectReadSchema = type('ProjectReadSchema', (Project, PydanticModel), {})
    ProjectCreateSchema = type('ProjectCreateSchema', (Project, PydanticModel), {})
    TaskReadSchema = type('TaskReadSchema', (Task, PydanticModel), {})
    TaskCreateSchema = type('TaskCreateSchema', (Task, PydanticModel), {})
```

## Configuration Options

### ConfigSchemaMeta

Use `ConfigSchemaMeta` for advanced configuration:

```python
from fastapi_mason.schemas import ConfigSchemaMeta

# Allow circular references in relationships
config = ConfigSchemaMeta(allow_cycles=True)

# Custom configuration
config = ConfigSchemaMeta(
    allow_cycles=True,
    exclude=('internal_field',),
    include=('custom_field',),
)

schema = generate_schema(
    Model,
    meta=ModelMeta,
    config=config
)
```

## Schema Naming

Control schema names for better OpenAPI documentation:

```python
# Explicit naming
UserReadSchema = generate_schema(
    User, 
    meta=UserMeta,
    name="UserResponse"
)

UserCreateSchema = rebuild_schema(
    UserReadSchema, 
    exclude_readonly=True,
    name="UserCreateRequest"
)
```

## Type Hints for IDE Support

Improve IDE support with type hints:

```python
from typing import TYPE_CHECKING
from tortoise.contrib.pydantic import PydanticModel

# Runtime schema generation
CompanySchema = generate_schema(Company, meta=CompanyMeta)

# Type hints for IDE
if TYPE_CHECKING:
    CompanySchema = type('CompanySchema', (Company, PydanticModel), {})
```

## Best Practices

### 1. Organize Meta Classes

```python
# Group related meta classes
class UserMetas:
    class Full(SchemaMeta):
        include = ('id', 'username', 'email', 'profile', 'created_at')
    
    class Public(SchemaMeta):
        include = ('id', 'username', 'created_at')
    
    class Minimal(SchemaMeta):
        include = ('id', 'username')

# Use specific meta for different contexts
PublicUserSchema = generate_schema(User, meta=UserMetas.Public)
```

### 2. Use Base Field Sets

```python
# Define common field sets
AUDIT_FIELDS = ('created_at', 'updated_at', 'created_by', 'updated_by')
BASE_FIELDS = ('id', *AUDIT_FIELDS)

class CompanyMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'description',
    )
```

### 3. Handle Sensitive Data

```python
class UserMeta(SchemaMeta):
    include = (
        'id',
        'username',
        'email',
        'profile',
    )
    exclude = (
        'password_hash',     # Never expose passwords
        'secret_key',        # Keep secrets private
        'internal_notes',    # Internal-only fields
    )
```

### 4. Version Your Schemas

```python
# API v1 schema
class CompanyV1Meta(SchemaMeta):
    include = ('id', 'name', 'description')

# API v2 schema with additional fields
class CompanyV2Meta(SchemaMeta):
    include = ('id', 'name', 'description', 'category', 'tags')

CompanyV1Schema = generate_schema(Company, meta=CompanyV1Meta, name="CompanyV1")
CompanyV2Schema = generate_schema(Company, meta=CompanyV2Meta, name="CompanyV2")
```

### 5. Document Your Schemas

```python
class CompanyMeta(SchemaMeta):
    """
    Schema configuration for Company model.
    
    Fields:
    - id: Primary key
    - name: Company display name
    - description: Optional company description
    - created_at: Creation timestamp
    - updated_at: Last modification timestamp
    """
    include = (
        'id',
        'name', 
        'description',
        'created_at',
        'updated_at',
    )
```

## Common Patterns

### API Response Schemas

```python
# Different schemas for different API responses
CompanyListSchema = generate_schema(Company, meta=CompanyListMeta)  # Minimal fields for lists
CompanyDetailSchema = generate_schema(Company, meta=CompanyDetailMeta)  # Full fields for details
CompanyCreateSchema = rebuild_schema(CompanyDetailSchema, exclude_readonly=True)
CompanyUpdateSchema = rebuild_schema(CompanyCreateSchema, exclude_readonly=True)
```

### Nested Resource Schemas

```python
# User with embedded profile
def get_user_with_profile_meta():
    return generate_schema_meta(
        UserMeta,
        ('profile', UserProfileMeta),
        ('preferences', UserPreferencesMeta),
    )

UserWithProfileSchema = generate_schema(
    User,
    meta=get_user_with_profile_meta(),
    config=ConfigSchemaMeta(allow_cycles=True)
)
```

The schema system in FastAPI Mason provides the flexibility to create exactly the API schemas you need while maintaining clean separation between your data models and API contracts. 