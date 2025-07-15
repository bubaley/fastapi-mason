from tortoise import fields

from app.core.models import BaseModel


class Company(BaseModel):
    name = fields.CharField(max_length=255)
    full_name = fields.TextField(null=True)

    class Meta:
        ordering = ['-id']
