class PollingIDError(Exception):
    """Raised when the polling ID cannot be retrieved on login."""

class LoginTimeout(TimeoutError):
    """Raised when the user didn't authorize the connection."""