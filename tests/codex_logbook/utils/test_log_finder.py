"""
Tests for Codex log discovery helpers.
"""

from unittest.mock import patch

import pytest

from codex_logbook.utils.log_finder import find_logs, get_all_projects_with_metadata, list_all_projects, validate_project_path


PROJECTS = [
    {
        "dir_name": "-Users-test-project1",
        "log_path": "/tmp/exports/-Users-test-project1",
        "file_count": 1,
        "total_size_mb": 0.01,
        "last_modified": 100,
        "first_seen": 90,
        "display_name": "/Users/test/project1",
        "source": "codex",
    },
    {
        "dir_name": "-Users-test-project2",
        "log_path": "/tmp/exports/-Users-test-project2",
        "file_count": 2,
        "total_size_mb": 0.02,
        "last_modified": 200,
        "first_seen": 80,
        "display_name": "/Users/test/project2",
        "source": "codex",
    },
]


def test_get_all_projects_with_metadata_returns_codex_exports():
    with patch("codex_logbook.utils.log_finder.get_codex_projects_metadata", return_value=PROJECTS):
        assert get_all_projects_with_metadata() == PROJECTS


def test_find_logs_matches_project_path():
    with patch("codex_logbook.utils.log_finder.get_codex_projects_metadata", return_value=PROJECTS):
        assert find_logs("/Users/test/project1") == "/tmp/exports/-Users-test-project1"


def test_find_logs_returns_none_when_project_is_unknown():
    with patch("codex_logbook.utils.log_finder.get_codex_projects_metadata", return_value=PROJECTS):
        assert find_logs("/Users/test/missing") is None


def test_list_all_projects_returns_display_names_and_paths():
    with patch("codex_logbook.utils.log_finder.get_codex_projects_metadata", return_value=PROJECTS):
        assert list_all_projects() == [
            ("/Users/test/project1", "/tmp/exports/-Users-test-project1"),
            ("/Users/test/project2", "/tmp/exports/-Users-test-project2"),
        ]


def test_validate_project_path_requires_existing_directory(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    dir_name = str(project_dir).replace("/", "-")
    projects = [{**PROJECTS[0], "dir_name": dir_name, "display_name": str(project_dir)}]

    with patch("codex_logbook.utils.log_finder.get_codex_projects_metadata", return_value=projects):
        valid, message = validate_project_path(str(project_dir))

    assert valid is True
    assert message == f"Found logs at: {projects[0]['log_path']}"


def test_validate_project_path_rejects_unknown_project(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    with patch("codex_logbook.utils.log_finder.get_codex_projects_metadata", return_value=[]):
        valid, message = validate_project_path(str(project_dir))

    assert valid is False
    assert message == f"No Codex logs found for project: {project_dir}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
