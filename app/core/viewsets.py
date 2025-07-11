from fastapi_mason.pagination import PageNumberPagination
from fastapi_mason.types import ModelType
from fastapi_mason.viewsets import ModelViewSet
from fastapi_mason.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper


class BaseModelViewSet(ModelViewSet[ModelType]):
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
