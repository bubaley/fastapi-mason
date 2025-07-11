from fastapi import APIRouter, Depends, Query

from app.core.viewsets import BaseModelViewSet
from app.domains.company.models import Company
from app.domains.company.schemas import CompanyCreateSchema, CompanySchema
from fastapi_mason import decorators
from fastapi_mason.permissions import IsAuthenticated
from fastapi_mason.state import BaseStateManager


async def auth_dependency(is_authenticated: bool = Query(default=False)):
    if is_authenticated:
        BaseStateManager.set_user({'id': 1, 'name': 'John Doe'})


router = APIRouter(prefix='/companies', tags=['companies'], dependencies=[Depends(auth_dependency)])


@decorators.viewset(router)
class CompanyViewSet(BaseModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.user:
            return Company.filter(id__lte=3)
        return Company.all()

    def get_permissions(self):
        if self.action in ('example', 'list'):
            return []
        return [IsAuthenticated()]

    @decorators.action(methods=['get'], detail=False)
    async def example(self):
        return '12312312'
