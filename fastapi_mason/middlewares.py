"""
Middleware system for FastAPI+ viewsets.

Provides middleware classes that can hook into viewset lifecycle events
to add cross-cutting concerns like logging, metrics, caching, etc.
"""

import logging
import time
from abc import ABC
from typing import Any, Dict, List, Optional

from fastapi import Request


class BaseViewSetMiddleware(ABC):
    """
    Abstract base class for viewset middleware.

    Middleware can hook into various points in the viewset lifecycle
    to add functionality like logging, metrics, caching, etc.
    """

    async def before_list(self, request: Request, viewset: Any, **kwargs) -> Optional[Any]:
        """
        Called before list action.

        Args:
            request: FastAPI request object
            viewset: ViewSet instance
            **kwargs: Additional context

        Returns:
            Optional response to short-circuit the action
        """
        pass

    async def after_list(self, request: Request, viewset: Any, response: Any, **kwargs) -> Any:
        """
        Called after list action.

        Args:
            request: FastAPI request object
            viewset: ViewSet instance
            response: Action response
            **kwargs: Additional context

        Returns:
            Modified response
        """
        return response

    async def before_retrieve(self, request: Request, viewset: Any, item_id: Any, **kwargs) -> Optional[Any]:
        """Called before retrieve action."""
        pass

    async def after_retrieve(self, request: Request, viewset: Any, response: Any, obj: Any, **kwargs) -> Any:
        """Called after retrieve action."""
        return response

    async def before_create(self, request: Request, viewset: Any, data: Any, **kwargs) -> Optional[Any]:
        """Called before create action."""
        pass

    async def after_create(self, request: Request, viewset: Any, response: Any, obj: Any, **kwargs) -> Any:
        """Called after create action."""
        return response

    async def before_update(self, request: Request, viewset: Any, item_id: Any, data: Any, **kwargs) -> Optional[Any]:
        """Called before update action."""
        pass

    async def after_update(self, request: Request, viewset: Any, response: Any, obj: Any, **kwargs) -> Any:
        """Called after update action."""
        return response

    async def before_destroy(self, request: Request, viewset: Any, item_id: Any, **kwargs) -> Optional[Any]:
        """Called before destroy action."""
        pass

    async def after_destroy(self, request: Request, viewset: Any, obj: Any, **kwargs) -> Any:
        """Called after destroy action."""
        pass

    async def before_action(self, request: Request, viewset: Any, action_name: str, **kwargs) -> Optional[Any]:
        """Called before any custom action."""
        pass

    async def after_action(self, request: Request, viewset: Any, action_name: str, response: Any, **kwargs) -> Any:
        """Called after any custom action."""
        return response

    async def on_exception(
        self, request: Request, viewset: Any, exception: Exception, action_name: str, **kwargs
    ) -> Optional[Any]:
        """
        Called when an exception occurs in any action.

        Returns:
            Optional response to handle the exception
        """
        pass


# Built-in middleware classes


class LoggingMiddleware(BaseViewSetMiddleware):
    """
    Middleware that logs viewset actions.

    Logs request/response information with configurable detail level.
    """

    def __init__(self, logger: Optional[logging.Logger] = None, log_level: int = logging.INFO):
        self.logger = logger or logging.getLogger(__name__)
        self.log_level = log_level

    async def before_list(self, request: Request, viewset: Any, **kwargs):
        """Log list request."""
        self.logger.log(
            self.log_level,
            f'List request for {viewset.__class__.__name__}',
            extra={
                'action': 'list',
                'viewset': viewset.__class__.__name__,
                'method': request.method,
                'url': str(request.url),
                'query_params': dict(request.query_params),
            },
        )

    async def after_list(self, request: Request, viewset: Any, response: Any, **kwargs):
        """Log list response."""
        result_count = len(response) if isinstance(response, list) else 'unknown'
        self.logger.log(
            self.log_level,
            f'List response for {viewset.__class__.__name__}: {result_count} items',
            extra={'action': 'list', 'viewset': viewset.__class__.__name__, 'result_count': result_count},
        )
        return response

    async def before_create(self, request: Request, viewset: Any, data: Any, **kwargs):
        """Log create request."""
        self.logger.log(
            self.log_level,
            f'Create request for {viewset.__class__.__name__}',
            extra={
                'action': 'create',
                'viewset': viewset.__class__.__name__,
                'data_fields': list(data.model_dump().keys()) if hasattr(data, 'model_dump') else 'unknown',
            },
        )

    async def on_exception(self, request: Request, viewset: Any, exception: Exception, action_name: str, **kwargs):
        """Log exceptions."""
        self.logger.error(
            f'Exception in {viewset.__class__.__name__}.{action_name}: {str(exception)}',
            extra={
                'action': action_name,
                'viewset': viewset.__class__.__name__,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
            },
            exc_info=True,
        )


class TimingMiddleware(BaseViewSetMiddleware):
    """
    Middleware that measures execution time of viewset actions.

    Can log timing information or send metrics to monitoring systems.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._start_times: Dict[str, float] = {}

    def _get_request_id(self, request: Request) -> str:
        """Get unique identifier for request."""
        return f'{id(request)}'

    async def before_list(self, request: Request, viewset: Any, **kwargs):
        """Start timing for list action."""
        self._start_times[self._get_request_id(request)] = time.time()

    async def after_list(self, request: Request, viewset: Any, response: Any, **kwargs):
        """Log timing for list action."""
        request_id = self._get_request_id(request)
        if request_id in self._start_times:
            duration = time.time() - self._start_times.pop(request_id)
            self.logger.info(
                f'List action for {viewset.__class__.__name__} took {duration:.3f}s',
                extra={'action': 'list', 'viewset': viewset.__class__.__name__, 'duration_seconds': duration},
            )
        return response

    async def before_create(self, request: Request, viewset: Any, data: Any, **kwargs):
        """Start timing for create action."""
        self._start_times[self._get_request_id(request)] = time.time()

    async def after_create(self, request: Request, viewset: Any, response: Any, obj: Any, **kwargs):
        """Log timing for create action."""
        request_id = self._get_request_id(request)
        if request_id in self._start_times:
            duration = time.time() - self._start_times.pop(request_id)
            self.logger.info(
                f'Create action for {viewset.__class__.__name__} took {duration:.3f}s',
                extra={'action': 'create', 'viewset': viewset.__class__.__name__, 'duration_seconds': duration},
            )
        return response


class CachingMiddleware(BaseViewSetMiddleware):
    """
    Simple caching middleware for viewset responses.

    This is a basic implementation. In production, you'd want to use
    Redis or similar for distributed caching.
    """

    def __init__(self, cache_timeout: int = 300):
        self.cache_timeout = cache_timeout
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, request: Request, viewset: Any, action: str, **kwargs) -> str:
        """Generate cache key for request."""
        base_key = f'{viewset.__class__.__name__}:{action}'

        # Add query parameters for list actions
        if action == 'list':
            query_params = sorted(request.query_params.items())
            query_string = '&'.join(f'{k}={v}' for k, v in query_params)
            return f'{base_key}?{query_string}'

        # Add item_id for detail actions
        item_id = kwargs.get('item_id')
        if item_id:
            return f'{base_key}:{item_id}'

        return base_key

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - cache_entry['timestamp'] < self.cache_timeout

    async def before_list(self, request: Request, viewset: Any, **kwargs):
        """Check cache for list response."""
        cache_key = self._get_cache_key(request, viewset, 'list', **kwargs)

        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry['response']  # Return cached response

        return None  # No cache hit, proceed with normal execution

    async def after_list(self, request: Request, viewset: Any, response: Any, **kwargs):
        """Cache list response."""
        cache_key = self._get_cache_key(request, viewset, 'list', **kwargs)
        self._cache[cache_key] = {'response': response, 'timestamp': time.time()}
        return response


# Middleware utilities


class MiddlewareManager:
    """
    Manager for viewset middleware execution.

    Handles the execution order and exception handling for middleware.
    """

    def __init__(self, middleware_classes: List[BaseViewSetMiddleware]):
        self.middleware_instances = middleware_classes

    async def run_before_hooks(self, action_name: str, request: Request, viewset: Any, **kwargs) -> Optional[Any]:
        """
        Run all before hooks for an action.

        Returns the first non-None response from middleware,
        which short-circuits the action execution.
        """
        hook_method = f'before_{action_name}'

        for middleware in self.middleware_instances:
            if hasattr(middleware, hook_method):
                result = await getattr(middleware, hook_method)(request, viewset, **kwargs)
                if result is not None:
                    return result  # Short-circuit

        return None

    async def run_after_hooks(self, action_name: str, request: Request, viewset: Any, response: Any, **kwargs) -> Any:
        """Run all after hooks for an action."""
        hook_method = f'after_{action_name}'

        for middleware in self.middleware_instances:
            if hasattr(middleware, hook_method):
                response = await getattr(middleware, hook_method)(request, viewset, response, **kwargs)

        return response

    async def handle_exception(
        self, action_name: str, request: Request, viewset: Any, exception: Exception, **kwargs
    ) -> Optional[Any]:
        """
        Handle exception through middleware.

        Returns the first non-None response from middleware,
        which handles the exception.
        """
        for middleware in self.middleware_instances:
            result = await middleware.on_exception(request, viewset, exception, action_name, **kwargs)
            if result is not None:
                return result  # Exception handled

        return None  # No middleware handled the exception
