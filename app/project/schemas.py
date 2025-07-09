from typing import TYPE_CHECKING

from tortoise.contrib.pydantic import PydanticModel, pydantic_model_creator

from app.project.models import Project

ProjectReadSchema = pydantic_model_creator(Project)
ProjectCreateSchema = pydantic_model_creator(Project, exclude_readonly=True)

if TYPE_CHECKING:
    ProjectReadSchema = type('ProjectReadSchema', (Project, PydanticModel), {})
    ProjectCreateSchema = type('ProjectCreateSchema', (Project, PydanticModel), {})
