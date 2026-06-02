"""
Shared data API utilities for consistent response formatting
"""

from typing import Any


def format_stats_response(statistics: dict[str, Any]) -> dict[str, Any]:
    """
    Format statistics for API response.
    """
    return statistics  # Already in the correct format from processor


def format_messages_response(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Format messages for API response.
    """
    return messages  # Already in the correct format from processor


def format_error_response(error: str, status_code: int = 500) -> dict[str, Any]:
    """Format error response consistently"""
    return {"error": True, "message": error, "status_code": status_code}


def format_success_response(message: str, data: Any = None) -> dict[str, Any]:
    """Format success response consistently"""
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return response
