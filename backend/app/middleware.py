"""Middleware for logging and monitoring requests."""

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .request_context import generate_request_id, set_request_id

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Skip WebSocket connections (middleware doesn't support them)
        if request.url.path.startswith('/ws'):
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Generate and set request ID in context
        request_id = generate_request_id()
        set_request_id(request_id)

        # Also store in request.state for easy access in route handlers
        request.state.request_id = request_id

        # Log incoming request
        logger.info(
            f'{request.method} {request.url.path}',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'client_host': request.client.host if request.client else None,
            },
        )

        # Process request
        try:
            response: Response = await call_next(request)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log response
            logger.info(
                f'{request.method} {request.url.path} - {response.status_code}',
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                },
            )

            # Add request ID to response headers for tracing
            response.headers['X-Request-ID'] = request_id

            return response

        except Exception as e:
            # Calculate duration even for errors
            duration_ms = int((time.time() - start_time) * 1000)

            # Log error
            logger.error(
                f'{request.method} {request.url.path} - Error: {str(e)}',
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'error': str(e),
                },
                exc_info=True,
            )

            # Re-raise the exception to be handled by error handlers
            raise
