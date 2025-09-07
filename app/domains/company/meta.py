from app.core.models import BASE_FIELDS
from fastapi_mason.schemas import SchemaMeta


class CompanyMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'full_name',
        'status',
    )
