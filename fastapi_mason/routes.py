"""
Utility functions for FastAPI+ core functionality.
"""

from typing import TYPE_CHECKING, Any, Callable, Dict

from fastapi.routing import APIRoute

if TYPE_CHECKING:
    from fastapi_mason.generics import GenericViewSet


BASE_ROUTE_PATHS = {
    'create': '/',
    'list': '/',
    'retrieve': '/{item_id}',
    'update': '/{item_id}',
    'destroy': '/{item_id}',
}


def sort_routes_by_specificity(routes: list[APIRoute]) -> list[APIRoute]:
    """
    Sort routes by specificity to ensure proper route matching.

    Routes with path parameters are considered less specific than static paths.
    HTTP methods are ordered by priority: GET, POST, PUT/PATCH, DELETE.

    Args:
        routes: List of FastAPI routes to sort

    Returns:
        Sorted list of routes
    """
    method_priority: Dict[str, int] = {
        'GET': 0,
        'POST': 1,
        'PUT': 2,
        'PATCH': 2,
        'DELETE': 3,
    }

    def route_score(route: APIRoute) -> tuple:
        """Calculate score for route sorting."""
        parts = route.path.strip('/').split('/')
        path_score = []

        for part in parts:
            if part.startswith('{') and part.endswith('}'):
                # Path parameter is less specific
                path_score.append(1)
            else:
                # Static path is more specific
                path_score.append(0)

        method_score = min(method_priority.get(method.upper(), 99) for method in route.methods)

        return (path_score, method_score)

    return sorted(routes, key=route_score)


def register_action_route(viewset: 'GenericViewSet', method: Callable):
    """
    Register a single action method as a route.

    Args:
        method_name: Name of the method
        method: Method object with action metadata
    """
    import inspect

    # Get action metadata
    action_methods = method._action_methods
    is_detail = method._action_detail

    action_path = method._action_path
    action_name = method._action_name or method.__name__
    action_response_model = method._action_response_model
    action_kwargs = getattr(method, '_action_kwargs', {})

    # Build the URL path
    # parts = []
    # if is_detail:
    #     parts.append("/{item_id}")
    # if action_path:
    #     parts.append(action_path)
    # path = "/" + "/".join(parts) if parts else "/"

    # full_path = viewset.router.prefix.rstrip("/") + path
    path = build_route_path(viewset.router.prefix, action_name, is_detail, action_path)

    routes_to_remove = []
    for route in viewset.router.routes:
        if isinstance(route, APIRoute):
            checks = [
                hasattr(route, 'name') and route.name == action_name,
                route.path_format == path and set(route.methods or []) & set(action_methods or []),
            ]
            if any(checks):
                routes_to_remove.append(route)

    for route in routes_to_remove:
        viewset.router.routes.remove(route)

    # Get original method signature and remove 'self'
    original_sig = inspect.signature(method)
    params = list(original_sig.parameters.values())[1:]  # Skip 'self'

    # Create new signature without 'self'
    new_signature = inspect.Signature(parameters=params, return_annotation=original_sig.return_annotation)

    # Create the endpoint function that preserves original signature
    def create_action_endpoint(action_name: str):
        # We need to create the function dynamically to preserve the exact signature

        async def action_endpoint(**endpoint_kwargs):
            """Action endpoint wrapper."""
            # Extract request if present
            request = endpoint_kwargs.get('request')

            # Check permissions
            if request:
                viewset.check_permissions(request)

            # For detail actions, check object permissions
            if is_detail and request:
                lookup_field = viewset._get_lookup_field()
                lookup_value = endpoint_kwargs.get(lookup_field)
                if lookup_value:
                    # Get object and check object-level permissions
                    await viewset.get_object(lookup_value, request)

            # Call the original action method with self and proper arguments
            # Map endpoint_kwargs to the original method parameters
            method_kwargs = {}
            for param in params:
                if param.name in endpoint_kwargs:
                    method_kwargs[param.name] = endpoint_kwargs[param.name]

            return await method(viewset, **method_kwargs)

        return action_endpoint

    action_endpoint = create_action_endpoint(action_name)

    # Set the correct signature for FastAPI documentation
    action_endpoint.__signature__ = new_signature
    action_endpoint.__name__ = method.__name__
    action_endpoint.__doc__ = method.__doc__

    # Copy annotations but remove 'self'
    annotations = getattr(method, '__annotations__', {}).copy()
    if 'self' in annotations:
        del annotations['self']
    action_endpoint.__annotations__ = annotations

    add_route(
        viewset=viewset,
        path=path,
        endpoint=action_endpoint,
        methods=action_methods,
        name=action_name,
        response_model=action_response_model,
        **action_kwargs,
    )


def add_route(
    viewset: 'GenericViewSet',
    path: str,
    endpoint: Any,
    methods: list[str],
    response_model: Any = None,
    status_code: int = 200,
    name: str = None,
    **kwargs,
):
    """
    Add a route to the viewset router.

    This method is used by mixins to add their specific routes.

    Args:
        path: URL path for the route
        endpoint: Endpoint function
        methods: HTTP methods
        response_model: Pydantic model for response
        status_code: HTTP status code
        name: Route name
        **kwargs: Additional FastAPI route parameters
    """
    # Check if route already exists
    existing_route_names = {route.name for route in viewset.router.routes}

    if name and name in existing_route_names:
        return  # Route already exists

    viewset.router.add_api_route(
        path=path,
        endpoint=endpoint,
        methods=methods,
        response_model=response_model,
        status_code=status_code,
        name=name,
        **kwargs,
    )


def build_route_path(
    prefix: str,
    action_name: str,
    is_detail: bool = False,
    action_path: str | None = None,
) -> str:
    if action_name in BASE_ROUTE_PATHS:
        return BASE_ROUTE_PATHS[action_name]
    elif action_path is None:
        action_path = action_name.replace('_', '-')

    parts = []
    if is_detail:
        parts.append('{item_id}')
    if action_path:
        cleaned_action_path = action_path.strip('/')
        if cleaned_action_path:
            parts.append(cleaned_action_path)
    path = '/' + '/'.join(parts)
    prefix = prefix.strip('/')
    return '/' + prefix + path if prefix else path
