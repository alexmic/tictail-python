"""
tictail.errors
~~~~~~~~~~~~~~

Custom exception classes.

"""

class ApiConnectionError(Exception):
    """Thrown if there was a problem with connecting to the api."""
    pass


class ApiError(Exception):
    """Base class for all HTTP errors. Adds two properties to the base `Exception`:

        * a `status` property representing the http status code returned with the error
        * a `http_body` property containing the body of the request.

    """
    def __init__(self, message, status, http_body):
        super(ApiError, self).__init__(message)
        self.message = message
        self.status = status
        self.http_body = http_body

    def __str__(self):
        return repr("{} (status: {})".format(self.message, self.status))


class ValidationError(ApiError):
    """Thrown for 422 errors."""
    pass


class Forbidden(ApiError):
    """Thrown for 403 errors, i.e auth issues."""
    pass


class NotFound(ApiError):
    """Thrown for 404 errors."""
    pass


class BadRequest(ApiError):
    """Thrown for 400 errors."""
    pass


class ServerError(ApiError):
    """Thrown for all errors apart from 400, 403, 404 and 422."""
    pass


__all__ = ('ClientError', 'ApiError', 'ApiConnectionError',
           'ApiValidationError', 'ApiAuthError', 'ApiServerError')