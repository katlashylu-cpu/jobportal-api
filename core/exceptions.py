from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class ConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A conflict occurred with the current state of the resource.'
    default_code = 'conflict'


def custom_exception_handler(exc, context):
    """
    Standardize all error responses to match PRD specification:
    {
      "error": {
        "code": "validation_error",
        "message": "Invalid input.",
        "details": { ... }
      }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code
        data = response.data

        # Determine error code and general message
        if status_code == 400:
            code = "validation_error"
            message = "Invalid input."
            details = data if isinstance(data, dict) else {"non_field_errors": data if isinstance(data, list) else [str(data)]}
        elif status_code == 401:
            code = "not_authenticated"
            message = data.get("detail", "Authentication credentials were not provided.") if isinstance(data, dict) else str(data)
            details = {}
        elif status_code == 403:
            code = "permission_denied"
            message = data.get("detail", "You do not have permission to perform this action.") if isinstance(data, dict) else str(data)
            details = {}
        elif status_code == 404:
            code = "not_found"
            message = data.get("detail", "Resource not found.") if isinstance(data, dict) else str(data)
            details = {}
        elif status_code == 409:
            code = "conflict"
            message = data.get("detail", "Resource conflict.") if isinstance(data, dict) else str(data)
            details = data if isinstance(data, dict) and "detail" not in data else {}
        elif status_code == 429:
            code = "throttled"
            message = data.get("detail", "Request was throttled.") if isinstance(data, dict) else str(data)
            details = {}
        else:
            code = "error"
            message = "An error occurred."
            details = data if isinstance(data, dict) else {"error": [str(data)]}

        # If details contains detail message alone, clean it up
        if isinstance(details, dict) and len(details) == 1 and "detail" in details:
            details = {}

        response.data = {
            "error": {
                "code": code,
                "message": str(message),
                "details": details
            }
        }

    return response
