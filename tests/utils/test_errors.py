"""Tests cho error handling utilities."""

import unittest

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.utils.errors import (
    APIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    add_exception_handlers,
    serialize_error,
)


class TestErrorUtils(unittest.TestCase):
    """Test cases cho error handling utils."""

    def test_api_error_base(self):
        """Test APIError base class."""
        error = APIError(message="Test error")

        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.error_code, "server_error")
        self.assertEqual(error.details, {})

    def test_validation_error(self):
        """Test ValidationError class."""
        details = {"field": "username", "issue": "too_short"}
        error = ValidationError(message="Validation failed", details=details)

        self.assertEqual(error.message, "Validation failed")
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.error_code, "validation_error")
        self.assertEqual(error.details, details)

    def test_authentication_error(self):
        """Test AuthenticationError class."""
        error = AuthenticationError(message="Invalid credentials")

        self.assertEqual(error.message, "Invalid credentials")
        self.assertEqual(error.status_code, 401)
        self.assertEqual(error.error_code, "authentication_error")

    def test_not_found_error(self):
        """Test NotFoundError class."""
        error = NotFoundError(message="Resource not found")

        self.assertEqual(error.message, "Resource not found")
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.error_code, "not_found")

    def test_serialize_error(self):
        """Test serialize_error function."""
        # Test with APIError
        error = ValidationError(
            message="Invalid input",
            details={"field": "email", "issue": "invalid_format"},
        )

        serialized = serialize_error(error)

        self.assertEqual(serialized["error"], "validation_error")
        self.assertEqual(serialized["message"], "Invalid input")
        self.assertEqual(serialized["details"]["field"], "email")
        self.assertEqual(serialized["details"]["issue"], "invalid_format")

        # Test with standard exception
        std_error = ValueError("Standard error")
        serialized = serialize_error(std_error)

        self.assertEqual(serialized["error"], "server_error")
        self.assertEqual(serialized["message"], "Standard error")

    def test_exception_handlers_integration(self):
        """Test add_exception_handlers integration with FastAPI."""
        app = FastAPI()

        # Add exception handlers
        add_exception_handlers(app)

        # Create test routes that raise different errors
        @app.get("/validation-error")
        async def validation_error_route():
            raise ValidationError(
                message="Validation failed",
                details={"field": "name", "issue": "required"},
            )

        @app.get("/auth-error")
        async def auth_error_route():
            raise AuthenticationError(message="Invalid token")

        @app.get("/not-found-error")
        async def not_found_error_route():
            raise NotFoundError(message="Campaign not found")

        @app.get("/generic-error")
        async def generic_error_route():
            raise ValueError("Something went wrong")

        # Create test client
        client = TestClient(app)

        # Test validation error
        response = client.get("/validation-error")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["error"], "validation_error")
        self.assertEqual(data["message"], "Validation failed")
        self.assertEqual(data["details"]["field"], "name")

        # Test authentication error
        response = client.get("/auth-error")
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data["error"], "authentication_error")
        self.assertEqual(data["message"], "Invalid token")

        # Test not found error
        response = client.get("/not-found-error")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["error"], "not_found")
        self.assertEqual(data["message"], "Campaign not found")

        # Test generic error
        response = client.get("/generic-error")
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data["error"], "server_error")
        self.assertEqual(data["message"], "Something went wrong")


if __name__ == "__main__":
    unittest.main()
