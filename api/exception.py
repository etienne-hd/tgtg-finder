class PollingIDError(RuntimeError):
    """Raised when the polling ID cannot be retrieved on login."""

class LoginTimeout(TimeoutError):
    """Raised when the user didn't authorize the connection."""

class DatadomeError(RuntimeError):
    """Raised when the client fails to generate a Datadome cookie."""

class NotAuthenticated(RuntimeError):
    """Raised when a method requiring authentication is called without being logged in."""

class RequestError(RuntimeError):
    """Raised when a request gets a 4xx status code response."""

class RequestUnauthorized(RequestError):
    """Raised on a 401 status code response."""

class RequestForbidden(RequestError):
    """Raised specifically on a 403 status code response."""

class RequestTooMany(RequestError):
    """Raised on a 429 Too Many Requests response."""