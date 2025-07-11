from app.domains.company.meta import CompanyMeta
from app.domains.company.models import Company
from fastapi_mason.schemas import generate_schema, rebuild_schema

CompanySchema = generate_schema(Company, meta=CompanyMeta)
CompanyCreateSchema = rebuild_schema(CompanySchema, exclude_readonly=True)
