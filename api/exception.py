class PollingIDError(RuntimeError):
    """Raised when the polling ID cannot be retrieved on login."""

class LoginTimeout(TimeoutError):
    """Raised when the user didn't authorize the connection."""

class DatadomeError(RuntimeError):
    """Raised when the client fails to generate a Datadome cookie."""

class NotAuthenticated(RuntimeError):
    """Raised when a method requiring authentication is called without being logged in."""

class TokenRefreshError(RuntimeError):
    """Raised when the JWT token cannot be refreshed."""