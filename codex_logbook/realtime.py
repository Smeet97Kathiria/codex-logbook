"""Realtime websocket coordination for Codex Logbook.

This module intentionally keeps websocket connection management and log-change
polling separate from the FastAPI route module. The server supplies app-specific
callbacks for cache refreshes and current-project state; this module owns the
transport contract.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

REALTIME_EVENT_VERSION = 1


@dataclass
class RealtimeClient:
    websocket: WebSocket
    subscribed_log_paths: set[str] | None = None
    connected_at: float = field(default_factory=time.time)
    last_seen_at: float = field(default_factory=time.time)
    missed_heartbeats: int = 0

    def matches(self, payload: dict[str, Any]) -> bool:
        """Return whether this client should receive a payload."""
        if self.subscribed_log_paths is None:
            return True

        payload_log_paths = set(payload.get("log_paths") or [])
        return bool(payload_log_paths & self.subscribed_log_paths)


class RealtimeUpdateHub:
    """Tracks websocket clients, subscriptions, and heartbeat cleanup."""

    def __init__(self, heartbeat_seconds: float = 30):
        self.heartbeat_seconds = heartbeat_seconds
        self._clients: dict[WebSocket, RealtimeClient] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._clients[websocket] = RealtimeClient(websocket=websocket)

    def disconnect(self, websocket: WebSocket):
        self._clients.pop(websocket, None)

    async def handle(self, websocket: WebSocket):
        """Accept and serve one websocket connection."""
        await self.connect(websocket)
        try:
            await websocket.send_json(self.envelope("connected", realtime=True))

            while True:
                try:
                    raw_message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=self.heartbeat_seconds,
                    )
                except asyncio.TimeoutError:
                    client = self._clients.get(websocket)
                    if client:
                        client.missed_heartbeats += 1
                        if client.missed_heartbeats > 2:
                            await websocket.close(code=1001)
                            self.disconnect(websocket)
                            return
                    await websocket.send_json(self.envelope("ping"))
                    continue

                await self.handle_client_message(websocket, raw_message)
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception:
            logger.debug("[Realtime] Closing websocket after connection error", exc_info=True)
            self.disconnect(websocket)

    async def handle_client_message(self, websocket: WebSocket, raw_message: str):
        client = self._clients.get(websocket)
        if not client:
            return

        client.last_seen_at = time.time()
        client.missed_heartbeats = 0

        if raw_message == "ping":
            await websocket.send_json(self.envelope("pong"))
            return

        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            await websocket.send_json(self.envelope("error", message="Invalid JSON message"))
            return

        message_type = message.get("type")
        if message_type == "pong":
            return

        if message_type == "subscribe":
            scope = message.get("scope")
            if scope == "overview":
                client.subscribed_log_paths = None
            else:
                log_paths = message.get("log_paths") or []
                client.subscribed_log_paths = {path for path in log_paths if isinstance(path, str)}

            await websocket.send_json(
                self.envelope(
                    "subscribed",
                    scope=scope or "projects",
                    log_paths=sorted(client.subscribed_log_paths) if client.subscribed_log_paths is not None else None,
                )
            )

    def envelope(self, event_type: str, **payload: Any) -> dict[str, Any]:
        return make_realtime_event(
            event_type,
            **payload,
        )

    async def broadcast(self, payload: dict[str, Any]):
        event = make_realtime_event(
            payload.get("type", "event"),
            **{key: value for key, value in payload.items() if key != "type"},
        )

        disconnected: list[WebSocket] = []
        for websocket, client in list(self._clients.items()):
            if not client.matches(event):
                continue

            try:
                await websocket.send_json(event)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)


def make_realtime_event(event_type: str, **payload: Any) -> dict[str, Any]:
    """Build a versioned realtime event envelope."""
    return {
            "version": REALTIME_EVENT_VERSION,
            "type": event_type,
            "created_at": time.time(),
            **payload,
        }


def log_files_signature(log_path: str) -> tuple[tuple[str, int, int], ...]:
    """Return a stable signature of JSONL files in a log directory."""
    path = Path(log_path)
    if not path.exists() or not path.is_dir():
        return ()

    signatures = []
    for file_path in path.glob("*.jsonl"):
        try:
            stat = file_path.stat()
            signatures.append((file_path.name, stat.st_size, stat.st_mtime_ns))
        except OSError:
            continue

    return tuple(sorted(signatures))


def collect_realtime_project_snapshots(
    current_project: Callable[[], tuple[str | None, str | None]],
) -> dict[str, dict[str, Any]]:
    """Refresh Codex exports and collect file signatures for known projects."""
    projects: list[dict[str, Any]] = []

    try:
        from codex_logbook.utils.log_finder import _get_projects_cached

        projects = _get_projects_cached(force_refresh=True)
    except Exception as e:
        logger.debug("[Realtime] Could not refresh Codex project exports: %s", e)
        try:
            from codex_logbook.utils.log_finder import get_all_projects_with_metadata

            projects = get_all_projects_with_metadata()
        except Exception as fallback_error:
            logger.debug("[Realtime] Could not load project metadata: %s", fallback_error)

    snapshots: dict[str, dict[str, Any]] = {}
    for project in projects:
        log_path = project.get("log_path")
        if not log_path:
            continue

        snapshots[log_path] = {
            "log_path": log_path,
            "dir_name": project.get("dir_name"),
            "display_name": project.get("display_name"),
            "signature": log_files_signature(log_path),
        }

    current_project_path, current_log_path = current_project()
    if current_log_path and current_log_path not in snapshots:
        snapshots[current_log_path] = {
            "log_path": current_log_path,
            "dir_name": Path(current_log_path).name,
            "display_name": current_project_path or Path(current_log_path).name,
            "signature": log_files_signature(current_log_path),
        }

    return snapshots


class RealtimeLogWatcher:
    """Polls Codex exports and broadcasts compact project update events."""

    def __init__(
        self,
        hub: RealtimeUpdateHub,
        collect_snapshots: Callable[[], dict[str, dict[str, Any]]],
        refresh_log_path: Callable[[str], Awaitable[dict[str, Any]]],
        get_current_log_path: Callable[[], str | None],
        initialize_log_paths: Callable[[list[str]], None] | None = None,
        poll_seconds: float = 2,
    ):
        self.hub = hub
        self.collect_snapshots = collect_snapshots
        self.refresh_log_path = refresh_log_path
        self.get_current_log_path = get_current_log_path
        self.initialize_log_paths = initialize_log_paths
        self.poll_seconds = max(poll_seconds, 0.5)
        self._stopped = asyncio.Event()

    def stop(self):
        self._stopped.set()

    async def run(self):
        logger.debug("[Realtime] Starting websocket update watcher")
        previous_snapshots = await asyncio.to_thread(self.collect_snapshots)
        if self.initialize_log_paths:
            self.initialize_log_paths(list(previous_snapshots.keys()))

        while not self._stopped.is_set():
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=self.poll_seconds)
                break
            except asyncio.TimeoutError:
                pass

            try:
                current_snapshots = await asyncio.to_thread(self.collect_snapshots)
                changed_projects = self.find_changed_projects(previous_snapshots, current_snapshots)
                previous_snapshots = current_snapshots

                if changed_projects:
                    await self.refresh_and_broadcast(changed_projects)
            except Exception as e:
                logger.error("[Realtime] Watcher error: %s", e)

    def find_changed_projects(
        self,
        previous_snapshots: dict[str, dict[str, Any]],
        current_snapshots: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        changed_projects = []

        for log_path, snapshot in current_snapshots.items():
            previous = previous_snapshots.get(log_path)
            if previous is None:
                if snapshot["signature"]:
                    changed_projects.append(snapshot)
            elif previous["signature"] != snapshot["signature"]:
                changed_projects.append(snapshot)

        return changed_projects

    async def refresh_and_broadcast(self, changed_projects: list[dict[str, Any]]):
        refreshed_projects = []

        for project in changed_projects:
            try:
                result = await self.refresh_log_path(project["log_path"])
                if result.get("files_changed"):
                    refreshed_projects.append(
                        {
                            "log_path": project["log_path"],
                            "dir_name": project.get("dir_name"),
                            "display_name": project.get("display_name"),
                            "stats": result.get("table_stats"),
                            "message_count": result.get("message_count"),
                            "refresh_time_ms": result.get("refresh_time_ms"),
                        }
                    )
            except Exception as refresh_error:
                logger.error("[Realtime] Failed to refresh %s: %s", project["log_path"], refresh_error)

        if not refreshed_projects:
            return

        await self.hub.broadcast(
            {
                "type": "dashboard_updated",
                "projects": refreshed_projects,
                "log_paths": [project["log_path"] for project in refreshed_projects],
                "current_log_path": self.get_current_log_path(),
            }
        )
