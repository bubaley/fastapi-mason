from enum import Enum

from tortoise import fields

from app.core.models import BaseModel


class CompanyStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class Company(BaseModel):
    name = fields.CharField(max_length=255)
    full_name = fields.TextField(null=True)
    status = fields.CharEnumField(max_length=255, enum_type=CompanyStatus, default=CompanyStatus.ACTIVE)

    class Meta:
        ordering = ['-id']
