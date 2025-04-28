"""Error handler utilities for API integrations."""

import logging
from typing import Any, Dict, Optional

from facebook_business.exceptions import FacebookRequestError
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class FacebookErrorHandler:
    """Handler for Facebook API errors."""

    def handle_error(self, error: Exception, context: str = "") -> None:
        """
        Handle Facebook API errors and raise appropriate HTTP exceptions.

        Args:
            error: The exception to handle
            context: Additional context about where the error occurred

        Raises:
            HTTPException: With appropriate status code and message
        """
        if isinstance(error, FacebookRequestError):
            error_code = error.api_error_code()
            error_subcode = error.api_error_subcode()
            error_message = error.api_error_message()

            # Log the error details with context if provided
            log_message = f"Facebook API Error: {error_message} (Code: {error_code}, Subcode: {error_subcode})"
            if context:
                log_message = f"{log_message} - Context: {context}"

            logger.error(log_message)

            # Authentication errors
            if error_code in (190, 102, 2500):
                raise HTTPException(
                    status_code=401,
                    detail=f"Facebook authentication error: {error_message}",
                )

            # Permission errors
            elif error_code in (10, 200, 299):
                raise HTTPException(
                    status_code=403,
                    detail=f"Facebook permission error: {error_message}",
                )

            # Rate limiting
            elif error_code == 613:
                raise HTTPException(
                    status_code=429,
                    detail="Facebook rate limit exceeded. Please try again later.",
                )

            # Resource not found
            elif error_code in (803, 100):
                raise HTTPException(
                    status_code=404,
                    detail=f"Facebook resource not found: {error_message}",
                )

            # Bad request errors
            elif error_code in (100, 302, 2):
                raise HTTPException(
                    status_code=400,
                    detail=f"Facebook API error: {error_message}",
                )

            # Default error handling
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Facebook API error: {error_message}",
                )
        else:
            # Handle other types of errors
            logger.error(f"Unexpected error in Facebook service: {str(error)}")
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(error)}"
            )
