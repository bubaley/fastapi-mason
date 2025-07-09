from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel
from tortoise.models import Model

if TYPE_CHECKING:
    pass


T = TypeVar('T')
SchemaType = TypeVar('SchemaType', bound=BaseModel)
ModelType = TypeVar('ModelType', bound=Model)
