from fastapi import APIRouter, Request

from app.project.models import Project
from app.project.schemas import ProjectCreateSchema, ProjectReadSchema
from fastapi_mason import decorators
from fastapi_mason.pagination import PageNumberPagination
from fastapi_mason.viewsets import ModelViewSet
from fastapi_mason.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper

router = APIRouter(tags=['projects'])


@decorators.viewset(router)
class ProjectViewSet(ModelViewSet[Project]):
    model = Project
    read_schema = ProjectReadSchema
    create_schema = ProjectCreateSchema
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper

    @decorators.action(methods=['GET'], response_model=ProjectReadSchema)
    async def penis(self, value: bool, penis: str, request: Request):
        if value:
            # self.requset = request
            setattr(self.requset, 'kekeke', '1')
            self.requset.state.penis = penis
        print(getattr(request.state, 'penis', None))
        print(getattr(request, 'kekeke', None))
        obj = await self.get_object(2)
        return await ProjectReadSchema.from_tortoise_orm(obj)

    # @decorators.action()
    # async def list(self):
    #     return "12312123"

    def get_queryset(self):
        return Project.filter(id__gt=3)

    @decorators.action(detail=True, methods=['POST'], response_model=ProjectReadSchema)
    async def supa_penis(self, kek: int):
        instance = await self.get_object(item_id=kek)
        data = await ProjectReadSchema.from_tortoise_orm(instance)
        return data
