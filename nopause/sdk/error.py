"""Error definitions for NoPause SDK."""

from typing import Optional

class APIError(Exception):
    """Base class for all NoPause API errors."""

    def __init__(self, message: str, code: Optional[int] = None):
        """Initialize an API error.

        Args:
            message: A human-readable error message.
            code: An optional error code.
        """
        self.message = message
        self.code = code

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"

    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


class InvalidRequestError(APIError):
    """Raised when the request is invalid."""


class NoPauseError(APIError):
    """Raised when the NoPause API returns an error."""
