import pytest

from codex_logbook import realtime


class FakeWebSocket:
    def __init__(self, fail=False):
        self.accepted = False
        self.closed = False
        self.sent = []
        self.fail = fail

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload):
        if self.fail:
            raise RuntimeError("send failed")
        self.sent.append(payload)

    async def close(self, code=1000):
        self.closed = code


def test_client_subscription_matching():
    overview_client = realtime.RealtimeClient(websocket=FakeWebSocket(), subscribed_log_paths=None)
    project_client = realtime.RealtimeClient(
        websocket=FakeWebSocket(),
        subscribed_log_paths={"/tmp/project-a"},
    )

    assert overview_client.matches({"log_paths": ["/tmp/project-b"]}) is True
    assert project_client.matches({"log_paths": ["/tmp/project-a"]}) is True
    assert project_client.matches({"log_paths": ["/tmp/project-b"]}) is False


@pytest.mark.asyncio
async def test_hub_subscribe_and_broadcast_filters_clients():
    hub = realtime.RealtimeUpdateHub()
    overview_socket = FakeWebSocket()
    project_socket = FakeWebSocket()
    failing_socket = FakeWebSocket(fail=True)

    await hub.connect(overview_socket)
    await hub.connect(project_socket)
    await hub.connect(failing_socket)
    await hub.handle_client_message(project_socket, '{"type":"subscribe","scope":"projects","log_paths":["/tmp/a"]}')
    await hub.handle_client_message(overview_socket, '{"type":"subscribe","scope":"overview"}')
    hub._clients[failing_socket].subscribed_log_paths = {"/tmp/a"}

    await hub.broadcast({"type": "dashboard_updated", "log_paths": ["/tmp/a"], "projects": []})
    await hub.broadcast({"type": "dashboard_updated", "log_paths": ["/tmp/b"], "projects": []})

    overview_events = [event["type"] for event in overview_socket.sent]
    project_events = [event["type"] for event in project_socket.sent]

    assert "subscribed" in overview_events
    assert overview_events.count("dashboard_updated") == 2
    assert project_events.count("dashboard_updated") == 1
    assert failing_socket not in hub._clients


@pytest.mark.asyncio
async def test_hub_rejects_invalid_json_and_plain_ping():
    hub = realtime.RealtimeUpdateHub()
    socket = FakeWebSocket()
    await hub.connect(socket)

    await hub.handle_client_message(socket, "not json")
    await hub.handle_client_message(socket, "ping")

    assert socket.sent[0]["type"] == "error"
    assert socket.sent[1]["type"] == "pong"


def test_log_file_signature_and_event_envelope(tmp_path):
    missing_signature = realtime.log_files_signature(str(tmp_path / "missing"))
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "b.jsonl").write_text("two\n", encoding="utf-8")
    (log_dir / "a.jsonl").write_text("one\n", encoding="utf-8")
    (log_dir / "ignored.txt").write_text("ignored\n", encoding="utf-8")

    signature = realtime.log_files_signature(str(log_dir))
    event = realtime.make_realtime_event("dashboard_updated", log_paths=["a"])

    assert missing_signature == ()
    assert [item[0] for item in signature] == ["a.jsonl", "b.jsonl"]
    assert event["version"] == realtime.REALTIME_EVENT_VERSION
    assert event["type"] == "dashboard_updated"
    assert event["log_paths"] == ["a"]


def test_collect_snapshots_uses_cached_projects_and_current_project(monkeypatch, tmp_path):
    project_dir = tmp_path / "project"
    current_dir = tmp_path / "current"
    project_dir.mkdir()
    current_dir.mkdir()
    (project_dir / "session.jsonl").write_text("{}\n", encoding="utf-8")
    (current_dir / "session.jsonl").write_text("{}\n", encoding="utf-8")

    def fake_projects(force_refresh=False):
        assert force_refresh is True
        return [
            {
                "log_path": str(project_dir),
                "dir_name": "project",
                "display_name": "Project",
            }
        ]

    monkeypatch.setattr("codex_logbook.utils.log_finder._get_projects_cached", fake_projects)

    snapshots = realtime.collect_realtime_project_snapshots(lambda: ("Current", str(current_dir)))

    assert set(snapshots) == {str(project_dir), str(current_dir)}
    assert snapshots[str(project_dir)]["display_name"] == "Project"
    assert snapshots[str(current_dir)]["display_name"] == "Current"


def test_watcher_detects_changes_and_new_projects():
    watcher = realtime.RealtimeLogWatcher(
        hub=realtime.RealtimeUpdateHub(),
        collect_snapshots=lambda: {},
        refresh_log_path=lambda log_path: {},
        get_current_log_path=lambda: None,
        poll_seconds=0.01,
    )

    previous = {
        "/tmp/a": {"log_path": "/tmp/a", "signature": (("a.jsonl", 1, 1),)},
        "/tmp/unchanged": {"log_path": "/tmp/unchanged", "signature": (("same.jsonl", 1, 1),)},
    }
    current = {
        "/tmp/a": {"log_path": "/tmp/a", "signature": (("a.jsonl", 2, 2),)},
        "/tmp/unchanged": {"log_path": "/tmp/unchanged", "signature": (("same.jsonl", 1, 1),)},
        "/tmp/new": {"log_path": "/tmp/new", "signature": (("new.jsonl", 1, 1),)},
        "/tmp/empty": {"log_path": "/tmp/empty", "signature": ()},
    }

    changed = watcher.find_changed_projects(previous, current)

    assert [project["log_path"] for project in changed] == ["/tmp/a", "/tmp/new"]


@pytest.mark.asyncio
async def test_watcher_refreshes_and_broadcasts_changed_projects():
    broadcasts = []

    class FakeHub:
        async def broadcast(self, payload):
            broadcasts.append(payload)

    async def refresh_log_path(log_path):
        if log_path.endswith("skip"):
            return {"files_changed": False}
        return {
            "files_changed": True,
            "table_stats": {"total_cost": 2.5},
            "message_count": 3,
            "refresh_time_ms": 12,
        }

    watcher = realtime.RealtimeLogWatcher(
        hub=FakeHub(),
        collect_snapshots=lambda: {},
        refresh_log_path=refresh_log_path,
        get_current_log_path=lambda: "/tmp/current",
        poll_seconds=0.01,
    )

    await watcher.refresh_and_broadcast(
        [
            {"log_path": "/tmp/project", "dir_name": "project", "display_name": "Project"},
            {"log_path": "/tmp/skip", "dir_name": "skip", "display_name": "Skip"},
        ]
    )

    assert len(broadcasts) == 1
    assert broadcasts[0]["type"] == "dashboard_updated"
    assert broadcasts[0]["log_paths"] == ["/tmp/project"]
    assert broadcasts[0]["projects"][0]["stats"] == {"total_cost": 2.5}
