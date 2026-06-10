"""Lightweight live counters for appended Codex JSONL activity.

The historical dashboard remains cache-backed. This module keeps tiny in-memory
increments for data appended after the cache baseline so realtime numbers can
move without reparsing or rewriting the full project cache on every tick.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codex_logbook.utils.pricing import calculate_cost

logger = logging.getLogger(__name__)


@dataclass
class LiveProjectDelta:
    file_offsets: dict[str, int] = field(default_factory=dict)
    file_mtimes: dict[str, int] = field(default_factory=dict)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read: int = 0
    total_cache_write: int = 0
    total_commands: int = 0
    total_cost: float = 0.0
    message_count: int = 0

    def as_table_delta(self) -> dict[str, Any]:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cache_read": self.total_cache_read,
            "total_cache_write": self.total_cache_write,
            "total_commands": self.total_commands,
            "total_cost": self.total_cost,
            "message_count": self.message_count,
        }


class LiveDeltaService:
    """Tracks appended JSONL bytes and cumulative in-memory live deltas."""

    def __init__(self):
        self._projects: dict[str, LiveProjectDelta] = {}

    def initialize_project(self, log_path: str):
        """Set file offsets to current EOF so future reads are append-only."""
        state = self._projects.setdefault(log_path, LiveProjectDelta())
        log_dir = Path(log_path)
        if not log_dir.exists() or not log_dir.is_dir():
            return

        for jsonl_file in log_dir.glob("*.jsonl"):
            try:
                stat = jsonl_file.stat()
                state.file_offsets[str(jsonl_file)] = stat.st_size
                state.file_mtimes[str(jsonl_file)] = stat.st_mtime_ns
            except OSError:
                continue

    def initialize_projects(self, log_paths: list[str]):
        for log_path in log_paths:
            self.initialize_project(log_path)

    def consume_project(self, log_path: str) -> dict[str, Any]:
        """Read newly appended lines and return the increment from this read."""
        state = self._projects.setdefault(log_path, LiveProjectDelta())
        log_dir = Path(log_path)
        increment = LiveProjectDelta()

        if not log_dir.exists() or not log_dir.is_dir():
            return increment.as_table_delta()

        for jsonl_file in sorted(log_dir.glob("*.jsonl")):
            self._consume_file(jsonl_file, state, increment)

        self._add_increment(state, increment)
        return increment.as_table_delta()

    def merged_table_stats(self, base_stats: dict[str, Any] | None, log_path: str) -> dict[str, Any] | None:
        """Return compact table stats with live deltas applied."""
        if base_stats is None:
            return None

        state = self._projects.get(log_path)
        if not state:
            return base_stats

        merged = dict(base_stats)
        merged["total_input_tokens"] = merged.get("total_input_tokens", 0) + state.total_input_tokens
        merged["total_output_tokens"] = merged.get("total_output_tokens", 0) + state.total_output_tokens
        merged["total_cache_read"] = merged.get("total_cache_read", 0) + state.total_cache_read
        merged["total_cache_write"] = merged.get("total_cache_write", 0) + state.total_cache_write
        merged["total_commands"] = merged.get("total_commands", 0) + state.total_commands
        merged["total_cost"] = merged.get("total_cost", 0) + state.total_cost
        return merged

    def project_delta(self, log_path: str) -> dict[str, Any]:
        state = self._projects.get(log_path)
        return state.as_table_delta() if state else LiveProjectDelta().as_table_delta()

    def reset_project(self, log_path: str):
        self._projects.pop(log_path, None)
        self.initialize_project(log_path)

    def _consume_file(self, jsonl_file: Path, state: LiveProjectDelta, increment: LiveProjectDelta):
        file_key = str(jsonl_file)
        try:
            stat = jsonl_file.stat()
        except OSError:
            return

        previous_offset = state.file_offsets.get(file_key)
        if previous_offset is None:
            previous_offset = 0
        elif stat.st_size < previous_offset:
            previous_offset = 0

        if stat.st_size == previous_offset:
            state.file_mtimes[file_key] = stat.st_mtime_ns
            return

        try:
            with open(jsonl_file, "r", encoding="utf-8", errors="replace") as file:
                file.seek(previous_offset)
                for line in file:
                    self._consume_line(line, increment)
                state.file_offsets[file_key] = file.tell()
                state.file_mtimes[file_key] = stat.st_mtime_ns
        except OSError as error:
            logger.debug("Failed to consume live delta from %s: %s", jsonl_file, error)

    def _consume_line(self, line: str, increment: LiveProjectDelta):
        line = line.strip()
        if not line:
            return

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return

        increment.message_count += 1
        if self._is_user_command(event):
            increment.total_commands += 1

        message = event.get("message") or {}
        usage = message.get("usage") or {}
        if not usage:
            return

        tokens = {
            "input": usage.get("input_tokens", 0),
            "output": usage.get("output_tokens", 0),
            "cache_creation": usage.get("cache_creation_input_tokens", 0),
            "cache_read": usage.get("cache_read_input_tokens", 0),
        }
        model = message.get("model") or event.get("model") or "gpt-5-mini"
        cost = calculate_cost(tokens, model)

        increment.total_input_tokens += tokens["input"]
        increment.total_output_tokens += tokens["output"]
        increment.total_cache_write += tokens["cache_creation"]
        increment.total_cache_read += tokens["cache_read"]
        increment.total_cost += cost["total_cost"]

    def _is_user_command(self, event: dict[str, Any]) -> bool:
        if event.get("type") != "user":
            return False

        message = event.get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            return not any(isinstance(item, dict) and item.get("type") == "tool_result" for item in content)

        return bool(content)

    def _add_increment(self, state: LiveProjectDelta, increment: LiveProjectDelta):
        state.total_input_tokens += increment.total_input_tokens
        state.total_output_tokens += increment.total_output_tokens
        state.total_cache_read += increment.total_cache_read
        state.total_cache_write += increment.total_cache_write
        state.total_commands += increment.total_commands
        state.total_cost += increment.total_cost
        state.message_count += increment.message_count
