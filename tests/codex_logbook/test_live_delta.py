import json

from codex_logbook.live_delta import LiveDeltaService


def append_jsonl(path, events):
    with open(path, "a", encoding="utf-8") as file:
        for event in events:
            if isinstance(event, str):
                file.write(event + "\n")
            else:
                file.write(json.dumps(event) + "\n")


def assistant_usage_event(input_tokens=1000, output_tokens=200, cache_read=300, cache_creation=40):
    return {
        "type": "assistant",
        "message": {
            "model": "gpt-5-mini",
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_creation,
            },
        },
    }


def test_initialize_project_starts_at_eof_and_consumes_only_appended_lines(tmp_path):
    log_dir = tmp_path / "project"
    log_dir.mkdir()
    jsonl_file = log_dir / "session.jsonl"
    append_jsonl(jsonl_file, [assistant_usage_event(input_tokens=500)])

    service = LiveDeltaService()
    service.initialize_project(str(log_dir))

    assert service.consume_project(str(log_dir))["message_count"] == 0

    append_jsonl(
        jsonl_file,
        [
            {"type": "user", "message": {"content": "build realtime updates"}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ignored"}]}},
            assistant_usage_event(input_tokens=1200, output_tokens=150, cache_read=700, cache_creation=50),
            "not json",
        ],
    )

    increment = service.consume_project(str(log_dir))
    delta = service.project_delta(str(log_dir))

    assert increment["message_count"] == 3
    assert increment["total_commands"] == 1
    assert increment["total_input_tokens"] == 1200
    assert increment["total_output_tokens"] == 150
    assert increment["total_cache_read"] == 700
    assert increment["total_cache_write"] == 50
    assert increment["total_cost"] > 0
    assert delta == increment


def test_merged_stats_and_reset_project(tmp_path):
    log_dir = tmp_path / "project"
    log_dir.mkdir()
    jsonl_file = log_dir / "session.jsonl"

    service = LiveDeltaService()
    append_jsonl(jsonl_file, [assistant_usage_event(input_tokens=250, output_tokens=75)])
    increment = service.consume_project(str(log_dir))

    base_stats = {
        "total_input_tokens": 100,
        "total_output_tokens": 20,
        "total_cache_read": 10,
        "total_cache_write": 5,
        "total_commands": 2,
        "total_cost": 1.25,
    }
    merged = service.merged_table_stats(base_stats, str(log_dir))

    assert merged["total_input_tokens"] == 100 + increment["total_input_tokens"]
    assert merged["total_output_tokens"] == 20 + increment["total_output_tokens"]
    assert merged["total_commands"] == 2
    assert merged["total_cost"] > base_stats["total_cost"]
    assert service.merged_table_stats(None, str(log_dir)) is None

    service.reset_project(str(log_dir))
    assert service.project_delta(str(log_dir))["message_count"] == 0


def test_file_truncation_resets_live_offset(tmp_path):
    log_dir = tmp_path / "project"
    log_dir.mkdir()
    jsonl_file = log_dir / "session.jsonl"

    service = LiveDeltaService()
    append_jsonl(jsonl_file, [assistant_usage_event(input_tokens=100)])
    assert service.consume_project(str(log_dir))["message_count"] == 1

    jsonl_file.write_text("", encoding="utf-8")
    append_jsonl(jsonl_file, [assistant_usage_event(input_tokens=300, output_tokens=25)])

    increment = service.consume_project(str(log_dir))

    assert increment["message_count"] == 1
    assert increment["total_input_tokens"] == 300
    assert increment["total_output_tokens"] == 25
