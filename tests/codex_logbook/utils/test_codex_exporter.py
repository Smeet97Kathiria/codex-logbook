import json
import sqlite3
from pathlib import Path

from codex_logbook.core.processor import CodexLogProcessor
from codex_logbook.utils.codex_exporter import get_codex_projects_metadata
from codex_logbook.utils.log_finder import find_logs


def _create_codex_state(codex_home: Path, rollout_path: Path):
    codex_home.mkdir(parents=True)
    connection = sqlite3.connect(codex_home / "state_5.sqlite")
    connection.execute(
        """
        CREATE TABLE threads (
            id TEXT PRIMARY KEY,
            rollout_path TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            cwd TEXT NOT NULL,
            title TEXT NOT NULL,
            tokens_used INTEGER NOT NULL DEFAULT 0,
            archived INTEGER NOT NULL DEFAULT 0,
            has_user_event INTEGER NOT NULL DEFAULT 0,
            cli_version TEXT NOT NULL DEFAULT '',
            first_user_message TEXT NOT NULL DEFAULT '',
            model TEXT
        )
        """
    )
    connection.execute(
        """
        INSERT INTO threads (
            id, rollout_path, created_at, updated_at, cwd, title, tokens_used,
            archived, has_user_event, cli_version, first_user_message, model
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "thread-1",
            str(rollout_path),
            1780000000,
            1780000060,
            "/tmp/demo-project",
            "Demo thread",
            123,
            0,
            1,
            "0.136.0",
            "Build a dashboard",
            "gpt-5",
        ),
    )
    connection.commit()
    connection.close()


def test_codex_exporter_materializes_processor_compatible_jsonl(tmp_path, monkeypatch):
    codex_home = tmp_path / ".codex"
    export_dir = tmp_path / "exports"
    rollout_path = tmp_path / "rollout.jsonl"
    rollout_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-06-02T12:00:01Z",
                        "type": "response_item",
                        "payload": {
                            "type": "function_call",
                            "name": "exec_command",
                            "arguments": '{"cmd": "pytest"}',
                            "call_id": "call-1",
                        },
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-06-02T12:00:02Z",
                        "type": "response_item",
                        "payload": {
                            "type": "function_call_output",
                            "call_id": "call-1",
                            "output": "passed",
                        },
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-06-02T12:00:03Z",
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "Tests pass."}],
                        },
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-06-02T12:00:04Z",
                        "type": "event_msg",
                        "payload": {
                            "type": "token_count",
                            "info": {
                                "last_token_usage": {
                                    "input_tokens": 100,
                                    "cached_input_tokens": 20,
                                    "output_tokens": 30,
                                }
                            },
                        },
                    }
                ),
            ]
        )
        + "\n"
    )
    _create_codex_state(codex_home, rollout_path)
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.setenv("CODEX_LOGBOOK_EXPORT_DIR", str(export_dir))

    projects = get_codex_projects_metadata(refresh=True)

    assert len(projects) == 1
    assert projects[0]["dir_name"] == "-tmp-demo-project"
    assert projects[0]["source"] == "codex"

    log_path = find_logs("/tmp/demo-project")
    assert log_path == projects[0]["log_path"]

    messages, stats = CodexLogProcessor(log_path).process_logs()
    assert len(messages) >= 3
    assert stats["overview"]["total_tokens"]["input"] == 100
    assert stats["overview"]["total_tokens"]["cache_read"] == 20
    assert stats["tools"]["usage_counts"]["exec_command"] == 1
