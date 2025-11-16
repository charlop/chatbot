"""
Global error handling middleware for FastAPI.
Catches all exceptions and returns standardized error responses.
"""

import logging
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.schemas.responses import ErrorResponse

logger = logging.getLogger(__name__)


async def error_handling_middleware(request: Request, call_next: Callable) -> Response:
    """
    Global error handling middleware.
    Catches all unhandled exceptions and returns standardized error responses.
    """
    try:
        response = await call_next(request)
        return response

    except ValidationError as e:
        # Pydantic validation errors (should be caught by FastAPI, but just in case)
        logger.warning(f"Validation error on {request.url.path}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="validation_error",
                message="Request validation failed",
                details=e.errors(),
                path=str(request.url.path),
            ).model_dump(),
        )

    except SQLAlchemyError as e:
        # Database errors
        logger.error(f"Database error on {request.url.path}: {str(e)}")
        logger.debug(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error="database_error",
                message="Database operation failed",
                details={"type": e.__class__.__name__},
                path=str(request.url.path),
            ).model_dump(),
        )

    except ValueError as e:
        # Business logic validation errors
        logger.warning(f"Value error on {request.url.path}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="invalid_request",
                message=str(e),
                path=str(request.url.path),
            ).model_dump(),
        )

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error on {request.url.path}: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred",
                details={"type": e.__class__.__name__},
                path=str(request.url.path),
            ).model_dump(),
        )
