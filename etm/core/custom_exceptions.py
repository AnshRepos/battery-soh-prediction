"""
ETM MCP Server Exception Management

Custom exceptions for ETM MCP Server.
"""


class ETMBaseException(Exception):
    """Base exception class for ETM MCP Server."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, object] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details: dict[str, object] = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AuthenticationError(ETMBaseException):
    """Raised when ETM authentication fails."""

    pass


class ResourceNotFoundError(ETMBaseException):
    """Raised when an ETM resource is not found."""

    pass


class APIRequestError(ETMBaseException):
    """Raised when an ETM API request fails."""

    pass


class XMLParseError(ETMBaseException):
    """Raised when XML parsing fails."""

    pass


class ConfigurationError(ETMBaseException):
    """Raised when ETM configuration is invalid."""

    pass
