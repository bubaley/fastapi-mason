from tortoise import fields
from tortoise.models import Model


class BaseModel(Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


BASE_FIELDS = ('id', 'created_at', 'updated_at')
