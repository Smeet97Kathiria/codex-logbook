# Codex Logbook CLI Reference

Complete reference for all Codex Logbook command-line interface commands.

## Command Overview

```
codex-logbook init          Start the analytics dashboard
codex-logbook config        Manage configuration
codex-logbook version       Show version information
codex-logbook help          Show help and usage examples
```

## Commands

### `codex-logbook init`

Start the Codex Logbook analytics dashboard server.

```bash
codex-logbook init [OPTIONS]
```

**Options:**
- `--port INTEGER` - Port to run server on (default: 8081)
- `--host STRING` - Host to run server on (default: localhost)
- `--no-browser` - Don't open browser automatically
- `--clear-cache` - Clear cached data

**Examples:**
```bash
codex-logbook init                    # Start with defaults
codex-logbook init --port 9000        # Use custom port
codex-logbook init --no-browser       # Don't open browser
```

---

### `codex-logbook config`

Manage configuration settings. This is a command group with subcommands:

#### `config show`

Display current configuration values and their sources.

```bash
codex-logbook config show [OPTIONS]
```

**Options:**
- `--json` - Output in JSON format

**Example output:**
```
Current configuration:
  auto_browser: True (default)
  port: 8090 (from config file)
  cache_max_projects: 5 (from environment)
```

#### `config set`

Set a configuration value.

```bash
codex-logbook config set KEY VALUE
```

**Examples:**
```bash
codex-logbook config set port 8090
codex-logbook config set auto_browser false
codex-logbook config set cache_max_projects 10
```

#### `config unset`

Remove a custom configuration value (revert to default).

```bash
codex-logbook config unset KEY
```

**Example:**
```bash
codex-logbook config unset port
```

---

### `codex-logbook version`

Show the current version of Codex Logbook.

```bash
codex-logbook version
```

---

### `codex-logbook help`

Show detailed help and usage examples.

```bash
codex-logbook help
```

## Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `port` | int | 8081 | Server port |
| `host` | str | 127.0.0.1 | Server host |
| `auto_browser` | bool | true | Auto-open browser |
| `cache_max_projects` | int | 5 | Max projects in memory |
| `cache_max_mb_per_project` | int | 500 | Max MB per project |
| `messages_initial_load` | int | 500 | Initial messages to load |
| `max_date_range_days` | int | 30 | Max days for date range |
| `enable_memory_monitor` | bool | false | Show memory usage |
| `enable_background_processing` | bool | true | Process stats in background |
| `cache_warm_on_startup` | int | 3 | Projects to preload |

## Environment Variables

All configuration keys can be set via environment variables:

```bash
# Examples
export PORT=9000
export AUTO_BROWSER=false
export CACHE_MAX_PROJECTS=10
export CODEX_HOME=/path/to/.codex
export CODEX_LOGBOOK_EXPORT_DIR=/path/to/codex-logbook-projects

# Or inline
PORT=9000 codex-logbook init
CODEX_HOME=/path/to/.codex codex-logbook init
```

**Mapping:**
- `port` → `PORT`
- `host` → `HOST`
- `auto_browser` → `AUTO_BROWSER`
- `cache_max_projects` → `CACHE_MAX_PROJECTS`
- `cache_max_mb_per_project` → `CACHE_MAX_MB_PER_PROJECT`
- etc. (uppercase with underscores)
- `CODEX_HOME` → Codex Desktop data directory to read from
- `CODEX_LOGBOOK_EXPORT_DIR` → generated project log directory to write to

## Configuration Priority

Settings are loaded in priority order:
1. Command-line arguments
2. Environment variables
3. Config file (`~/.codex-logbook/config.json`)
4. Built-in defaults

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Invalid command or arguments

## File Locations

- **Configuration**: `~/.codex-logbook/config.json`
- **Codex source data**: `~/.codex/state_5.sqlite` plus rollout JSONL files referenced by that database
- **Generated project logs**: `~/.codex-logbook/codex/projects/`
- **Cache**: `~/.codex-logbook/cache/`
