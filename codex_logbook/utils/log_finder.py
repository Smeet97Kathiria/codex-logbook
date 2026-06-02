"""
Utilities to find local AI coding assistant logs for a given project path.
"""

import logging
import os
import time
from .codex_exporter import get_codex_projects_metadata

logger = logging.getLogger(__name__)

_PROJECTS_CACHE: list[dict] | None = None
_PROJECTS_CACHE_AT = 0.0
_PROJECTS_CACHE_SOURCE_ID: int | None = None
_PROJECTS_CACHE_TTL_SECONDS = 15


def _get_projects_cached(force_refresh: bool = False) -> list[dict]:
    """Return project metadata without re-exporting Codex logs on every request."""
    global _PROJECTS_CACHE, _PROJECTS_CACHE_AT, _PROJECTS_CACHE_SOURCE_ID

    now = time.monotonic()
    source_id = id(get_codex_projects_metadata)
    if (
        not force_refresh
        and _PROJECTS_CACHE is not None
        and _PROJECTS_CACHE_SOURCE_ID == source_id
        and now - _PROJECTS_CACHE_AT < _PROJECTS_CACHE_TTL_SECONDS
    ):
        return [project.copy() for project in _PROJECTS_CACHE]

    refresh = force_refresh or _PROJECTS_CACHE is None
    projects = get_codex_projects_metadata(refresh=refresh)
    _PROJECTS_CACHE = [project.copy() for project in projects]
    _PROJECTS_CACHE_AT = now
    _PROJECTS_CACHE_SOURCE_ID = source_id
    return projects


def find_logs(project_path: str) -> str | None:
    """
    Find exported Codex logs for a project path.
    """
    project_path = os.path.abspath(project_path).rstrip("/")
    converted_path = project_path.replace("/", "-")

    for project in _get_projects_cached():
        if project["dir_name"] == converted_path:
            return project["log_path"]

    return None


def list_all_projects() -> list:
    """
    List all Codex projects found on the system.
    """
    return [(project["display_name"], project["log_path"]) for project in _get_projects_cached()]


def validate_project_path(project_path: str) -> tuple[bool, str]:
    """
    Validate a project path and return status with message.

    Returns:
        (is_valid, message)
    """
    if not project_path:
        return False, "Project path cannot be empty"

    if not os.path.exists(project_path):
        return False, f"Project path does not exist: {project_path}"

    if not os.path.isdir(project_path):
        return False, f"Project path must be a directory: {project_path}"

    # Check if logs exist
    log_path = find_logs(project_path)
    if not log_path:
        return False, f"No Codex logs found for project: {project_path}"

    return True, f"Found logs at: {log_path}"


def get_all_projects_with_metadata() -> list[dict]:
    """
    Get all Codex projects with metadata for fast display.

    Returns metadata without reading file contents for performance.

    Returns:
        List of dictionaries containing:
        - dir_name: Directory name in ~/.codex-logbook/codex/projects
        - log_path: Full path to log directory
        - file_count: Number of JSONL files
        - total_size_mb: Total size of JSONL files in MB
        - last_modified: Unix timestamp of most recent modification
        - first_seen: Unix timestamp of earliest file (approximation of first use)
        - display_name: Human-readable project name
    """
    return _get_projects_cached()
