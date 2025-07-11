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
