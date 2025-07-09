"""
Mixins for FastAPI+ viewsets.

These mixins only add specific routes to the GenericViewSet.
They do not contain any business logic - all logic is in GenericViewSet.
"""

from typing import TYPE_CHECKING

from fastapi import Depends, Request

from fastapi_mason.routes import BASE_ROUTE_PATHS, add_route

if TYPE_CHECKING:
    from fastapi_mason.generics import GenericViewSet


class ListMixin:
    """
    Mixin that adds list endpoint to GenericViewSet.

    Adds:
    - GET / - list all objects with pagination support
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_list_route()

    def add_list_route(self: 'GenericViewSet'):
        """Add list route to the viewset."""
        ACTION = 'list'

        async def list_endpoint(
            request: Request,
            pagination=Depends(self.pagination.from_query),
        ):
            """List all objects with optional pagination."""
            request.state.action = ACTION
            # Check permissions
            self.check_permissions(request)

            # Get filtered queryset
            queryset = await self.get_filtered_queryset(request)

            if (
                not isinstance(pagination, type(self.pagination()))
                or hasattr(pagination, 'offset')
                or hasattr(pagination, 'page')
            ):
                return await self.get_paginated_response(queryset=queryset, pagination=pagination)

            results = await self.many_read_schema.from_queryset(queryset)

            if self.list_wrapper:
                return self.list_wrapper.wrap(data=results, pagination=pagination)

            return results

        add_route(
            self,
            path=BASE_ROUTE_PATHS[ACTION],
            endpoint=list_endpoint,
            methods=['GET'],
            response_model=self.get_list_response_model(),
            name=ACTION,
        )


class RetrieveMixin:
    """
    Mixin that adds retrieve endpoint to GenericViewSet.

    Adds:
    - GET /{item_id} - retrieve single object by ID

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_retrieve_route()

    def add_retrieve_route(self: 'GenericViewSet'):
        """Add retrieve route to the viewset."""
        ACTION = 'retrieve'

        async def retrieve_endpoint(item_id: int, request: Request):
            """Retrieve single object by ID."""
            request.state.action = ACTION
            # Check permissions (both general and object-level)
            obj = await self.get_object(item_id, request)
            result = await self.read_schema.from_tortoise_orm(obj)

            if self.single_wrapper:
                return self.single_wrapper.wrap(data=result)

            return result

        add_route(
            self,
            path=BASE_ROUTE_PATHS[ACTION],
            endpoint=retrieve_endpoint,
            methods=['GET'],
            response_model=self.get_single_response_model(),
            name=ACTION,
        )


class CreateMixin:
    """
    Mixin that adds create endpoint to GenericViewSet.

    Adds:
    - POST / - create new object
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_create_route()

    def add_create_route(self: 'GenericViewSet'):
        """Add create route to the viewset."""
        ACTION = 'create'

        async def create_endpoint(data: self.create_schema, request: Request):
            """Create new object."""
            request.state.action = ACTION
            # Check permissions
            self.check_permissions(request)

            obj_data = data.model_dump(exclude_unset=True)
            obj = self.model(**obj_data)
            obj = await self.perform_create(obj, request)
            result = await self.read_schema.from_tortoise_orm(obj)

            if self.single_wrapper:
                return self.single_wrapper.wrap(data=result)

            return result

        add_route(
            self,
            path=BASE_ROUTE_PATHS[ACTION],
            endpoint=create_endpoint,
            methods=['POST'],
            response_model=self.get_single_response_model(),
            status_code=201,
            name=ACTION,
        )


class UpdateMixin:
    """
    Mixin that adds update endpoint to GenericViewSet.

    Adds:
    - PUT /{item_id} - update object (full update)
    - PATCH /{item_id} - update object (partial update)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_update_route()

    def add_update_route(self: 'GenericViewSet'):
        """Add update route to the viewset."""
        ACTION = 'update'

        async def update_endpoint(item_id: int, data: self.update_schema, request: Request):
            """Update existing object."""
            request.state.action = ACTION
            # Check permissions (both general and object-level)
            obj = await self.get_object(item_id, request)

            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(obj, key, value)

            obj = await self.perform_update(obj, request)
            result = await self.read_schema.from_tortoise_orm(obj)

            if self.single_wrapper:
                return self.single_wrapper.wrap(data=result)

            return result

        add_route(
            self,
            path=BASE_ROUTE_PATHS[ACTION],
            endpoint=update_endpoint,
            methods=['PUT', 'PATCH'],
            response_model=self.get_single_response_model(),
            name=ACTION,
        )


class DestroyMixin:
    """
    Mixin that adds destroy endpoint to GenericViewSet.

    Adds:
    - DELETE /{item_id} - delete object
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_destroy_route()

    def add_destroy_route(self: 'GenericViewSet'):
        """Add destroy route to the viewset."""
        ACTION = 'destroy'

        async def destroy_endpoint(item_id: int, request: Request):
            """Delete object by ID."""
            request.state.action = ACTION
            # Check permissions (both general and object-level)
            obj = await self.get_object(item_id, request)
            await self.perform_destroy(obj, request)

        add_route(
            self,
            path=BASE_ROUTE_PATHS[ACTION],
            endpoint=destroy_endpoint,
            methods=['DELETE'],
            status_code=204,
            name=ACTION,
        )
