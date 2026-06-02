"""
Export Codex Desktop sessions into Codex Logbook-compatible JSONL project folders.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CODEX_HOME_ENV = "CODEX_HOME"
CODEX_EXPORT_DIR_ENV = "CODEX_LOGBOOK_EXPORT_DIR"


def codex_home() -> Path:
    return Path(os.getenv(CODEX_HOME_ENV, Path.home() / ".codex")).expanduser()


def codex_export_base() -> Path:
    configured = os.getenv(CODEX_EXPORT_DIR_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex-logbook" / "codex" / "projects"


def is_codex_available() -> bool:
    return (codex_home() / "state_5.sqlite").exists()


def _project_dir_name(cwd: str) -> str:
    normalized = os.path.abspath(cwd).rstrip("/")
    return normalized.replace("/", "-") or "unknown"


def _iso_from_epoch(value: int | float | None) -> str:
    if not value:
        return ""
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"text", "output_text", "input_text"}:
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(part for part in parts if part)
    return ""


def _base_entry(thread: dict[str, Any], timestamp: str, uuid: str, entry_type: str) -> dict[str, Any]:
    return {
        "parentUuid": None,
        "isSidechain": False,
        "userType": "external",
        "cwd": thread.get("cwd", ""),
        "sessionId": thread["id"],
        "version": thread.get("cli_version", ""),
        "type": entry_type,
        "uuid": uuid,
        "timestamp": timestamp,
    }


def _codex_user_message(thread: dict[str, Any], timestamp: str, content: str, uuid: str) -> dict[str, Any]:
    entry = _base_entry(thread, timestamp, uuid, "user")
    entry["message"] = {"role": "user", "content": content}
    return entry


def _codex_assistant_message(
    thread: dict[str, Any],
    timestamp: str,
    content: str,
    uuid: str,
    usage: dict[str, int] | None = None,
) -> dict[str, Any]:
    usage = usage or {}
    entry = _base_entry(thread, timestamp, uuid, "assistant")
    entry["requestId"] = uuid
    entry["message"] = {
        "id": f"msg_{uuid}",
        "type": "message",
        "role": "assistant",
        "model": thread.get("model") or "codex",
        "content": [{"type": "text", "text": content}],
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": usage.get("cached_input_tokens", 0),
        },
    }
    return entry


def _codex_tool_message(thread: dict[str, Any], timestamp: str, payload: dict[str, Any], uuid: str) -> dict[str, Any]:
    try:
        arguments = json.loads(payload.get("arguments") or "{}")
    except json.JSONDecodeError:
        arguments = {"arguments": payload.get("arguments", "")}

    entry = _base_entry(thread, timestamp, uuid, "assistant")
    entry["requestId"] = uuid
    entry["message"] = {
        "id": f"msg_{uuid}",
        "type": "message",
        "role": "assistant",
        "model": thread.get("model") or "codex",
        "content": [
            {
                "type": "tool_use",
                "id": payload.get("call_id", uuid),
                "name": payload.get("name", "tool"),
                "input": arguments,
            }
        ],
        "stop_reason": "tool_use",
        "usage": {},
    }
    return entry


def _codex_tool_result_message(thread: dict[str, Any], timestamp: str, payload: dict[str, Any], uuid: str) -> dict[str, Any]:
    entry = _base_entry(thread, timestamp, uuid, "user")
    entry["message"] = {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": payload.get("call_id", ""),
                "content": payload.get("output", ""),
                "is_error": False,
            }
        ],
    }
    return entry


def _read_rollout_events(thread: dict[str, Any]) -> list[dict[str, Any]]:
    rollout_path = Path(thread.get("rollout_path") or "")
    if not rollout_path.exists():
        return []

    events = []
    last_text = ""
    for index, line in enumerate(rollout_path.read_text(errors="replace").splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        timestamp = event.get("timestamp") or _iso_from_epoch(thread.get("updated_at"))
        payload = event.get("payload") or {}

        if event.get("type") == "response_item":
            uuid = f"{thread['id']}-{index}"
            if payload.get("type") == "message" and payload.get("role") == "assistant":
                text = _extract_text(payload.get("content"))
                if text:
                    last_text = text
                    events.append(_codex_assistant_message(thread, timestamp, text, uuid))
            elif payload.get("type") == "function_call":
                events.append(_codex_tool_message(thread, timestamp, payload, uuid))
            elif payload.get("type") == "function_call_output":
                events.append(_codex_tool_result_message(thread, timestamp, payload, uuid))

        elif event.get("type") == "event_msg" and payload.get("type") == "token_count":
            usage = payload.get("info", {}).get("last_token_usage") or {}
            if any(usage.get(key, 0) for key in ("input_tokens", "output_tokens", "cached_input_tokens")):
                uuid = f"{thread['id']}-{index}-usage"
                events.append(_codex_assistant_message(thread, timestamp, last_text or "Codex turn completed.", uuid, usage))
                last_text = ""

    return events


def _connect_state_db() -> sqlite3.Connection | None:
    db_path = codex_home() / "state_5.sqlite"
    if not db_path.exists():
        return None
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def load_codex_threads() -> list[dict[str, Any]]:
    connection = _connect_state_db()
    if connection is None:
        return []
    try:
        rows = connection.execute(
            """
            SELECT id, rollout_path, created_at, updated_at, cwd, title, tokens_used,
                   cli_version, first_user_message, model
            FROM threads
            WHERE archived = 0 AND (first_user_message != '' OR title != '')
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def refresh_codex_exports() -> list[dict[str, Any]]:
    projects: dict[str, dict[str, Any]] = {}
    for thread in load_codex_threads():
        dir_name = _project_dir_name(thread.get("cwd", ""))
        project_dir = codex_export_base() / dir_name
        project_dir.mkdir(parents=True, exist_ok=True)

        first_user_message = thread.get("first_user_message") or thread.get("title") or "Codex session"
        messages = [
            _codex_user_message(
                thread,
                _iso_from_epoch(thread.get("created_at")),
                first_user_message,
                f"{thread['id']}-user",
            )
        ]
        messages.extend(_read_rollout_events(thread))

        output_path = project_dir / f"{thread['id']}.jsonl"
        output_text = "\n".join(json.dumps(message, ensure_ascii=False) for message in messages) + "\n"
        if not output_path.exists() or output_path.read_text(errors="replace") != output_text:
            output_path.write_text(output_text)

        project = projects.setdefault(
            dir_name,
            {
                "dir_name": dir_name,
                "log_path": str(project_dir),
                "file_count": 0,
                "total_size_mb": 0,
                "last_modified": 0,
                "first_seen": thread.get("created_at") or 0,
                "display_name": thread.get("cwd", dir_name),
                "source": "codex",
            },
        )
        project["file_count"] += 1
        project["last_modified"] = max(project["last_modified"], thread.get("updated_at") or 0)
        project["first_seen"] = min(project["first_seen"], thread.get("created_at") or project["first_seen"])

    for project in projects.values():
        jsonl_files = list(Path(project["log_path"]).glob("*.jsonl"))
        project["total_size_mb"] = round(sum(path.stat().st_size for path in jsonl_files) / (1024 * 1024), 2)

    return list(projects.values())


def get_codex_projects_metadata(refresh: bool = True) -> list[dict[str, Any]]:
    if not is_codex_available():
        return []
    if refresh:
        return refresh_codex_exports()

    projects = []
    base = codex_export_base()
    if not base.exists():
        return projects
    for log_dir in base.iterdir():
        if not log_dir.is_dir():
            continue
        jsonl_files = list(log_dir.glob("*.jsonl"))
        if not jsonl_files:
            continue
        mtimes = [path.stat().st_mtime for path in jsonl_files]
        projects.append(
            {
                "dir_name": log_dir.name,
                "log_path": str(log_dir),
                "file_count": len(jsonl_files),
                "total_size_mb": round(sum(path.stat().st_size for path in jsonl_files) / (1024 * 1024), 2),
                "last_modified": max(mtimes),
                "first_seen": min(mtimes),
                "display_name": log_dir.name,
                "source": "codex",
            }
        )
    return projects


def export_codex_project(log_dir_name: str) -> str | None:
    for project in get_codex_projects_metadata(refresh=True):
        if project["dir_name"] == log_dir_name:
            return project["log_path"]
    return None
