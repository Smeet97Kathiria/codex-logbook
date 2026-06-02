# Codex Logbook

<p align="center">
  <img src="assets/codex_logbook/logo-orange.svg" width="96" alt="Codex Logbook logo">
</p>

<p align="center">
  <strong>A local, privacy-first dashboard for seeing what your Codex sessions are really doing.</strong>
</p>

<p align="center">
  <a href="https://github.com/Smeet97Kathiria/codex-logbook/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/Smeet97Kathiria/codex-logbook?style=flat&label=stars&color=f97316"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-f97316"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-2563eb">
  <img alt="Built for OpenAI Codex" src="https://img.shields.io/badge/built%20for-OpenAI%20Codex-412991">
  <img alt="Local first" src="https://img.shields.io/badge/local--first-dashboard-16a34a">
  <img alt="No telemetry" src="https://img.shields.io/badge/no-telemetry-111827">
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/Smeet97Kathiria/codex-logbook?label=updated&color=64748b">
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> ·
  <a href="#why-codex-logbook">Why Codex Logbook</a> ·
  <a href="#features">Features</a> ·
  <a href="#privacy">Privacy</a> ·
  <a href="#development">Development</a>
</p>

<p align="center">
  <img src="assets/screenshots/codex-logbook-overview.png" width="1000" alt="Codex Logbook project overview dashboard">
</p>

I built Codex Logbook because Codex usage gets hard to understand once you use it across a bunch of real projects. The app reads your local Codex logs and shows where tokens, cost, tools, commands, and project activity are piling up, without sending your logs to a third-party analytics service.

## Quickstart

Requirement: **Python 3.10+**

### From Source

```bash
git clone https://github.com/Smeet97Kathiria/codex-logbook.git
cd codex-logbook

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
codex-logbook init
```

Open the dashboard at:

```text
http://127.0.0.1:8081
```

### With uv

```bash
uvx codex-logbook@latest init
```

Or install it as a uv tool:

```bash
uv tool install codex-logbook@latest
codex-logbook init
```

### With pip

```bash
pip install codex-logbook
codex-logbook init
```

## Why Codex Logbook

Once Codex becomes part of your daily workflow, the questions get practical fast:

- Which projects are using the most tokens?
- Where are estimated costs concentrated?
- Which prompts create long tool chains?
- How often does Codex need tools to complete work?
- Which projects are active, stale, expensive, or context-heavy?
- Where can better prompts reduce token waste?

Codex Logbook is meant for those check-ins: open it, spot what changed, and make better calls about prompts, context, and token budget.

## Features

- **Project overview**: See which Codex projects are active, expensive, token-heavy, or missing data.
- **Token and cost charts**: Track input/output tokens and estimated direct API cost over time.
- **Tool usage breakdowns**: Find sessions that rely heavily on terminal, file, browser, or other tools.
- **Command review**: Look back at commands, step counts, tool counts, models, token estimates, and interruptions.
- **Message and JSONL viewers**: Search parsed messages or inspect the original log lines when you need the source of truth.
- **Local by default**: Process logs on your machine and serve the dashboard from localhost.
- **Optional sharing**: Publish a dashboard only when you intentionally create a share link.

## Privacy

> Privacy is the default, not an add-on. Codex Logbook runs locally, has no telemetry, and does not upload your logs in the background.

- Local log processing
- Local dashboard by default
- No tracking scripts
- No usage telemetry
- No background upload
- Optional share workflow only when you intentionally publish a dashboard

Always review command text before sharing. Your commands may include private project details, file paths, or sensitive context.

## What You Can See

These are the signals I wanted at a glance:

| Signal | Why it matters |
| --- | --- |
| Token volume | Which projects consume the most input/output tokens |
| Estimated cost | Where direct API cost would concentrate |
| Tool usage | How often Codex relies on terminal, file, or browser tools |
| Steps per command | Which requests create long execution chains |
| Prompt cache read | How much context reuse appears in your logs |
| Project activity | Which projects are active, stale, or data-heavy |
| Command history | Which requests produced expensive or complex sessions |

## Dashboard Tour

The overview is for scanning everything quickly. The project page is for digging into one Codex workspace when something looks expensive, noisy, or unusually tool-heavy.

<p align="center">
  <img src="assets/screenshots/codex-logbook-project-summary.png" width="1000" alt="Codex Logbook project analytics summary">
</p>

<p align="center">
  <strong>Project analytics:</strong> inspect command behavior, tool use, interruption rate, cache reads, and cost signals inside a project.
</p>

<p align="center">
  <img src="assets/screenshots/codex-logbook-project-charts.png" width="1000" alt="Codex Logbook project chart breakdowns">
</p>

<p align="center">
  <strong>Chart breakdowns:</strong> review tool trends, daily costs, token usage, and tool distribution for better Codex workflow decisions.
</p>

## Perfect For

- Developers who use Codex every day
- Builders who want to understand token and cost patterns
- Teams reviewing how AI coding work actually happens
- Power users tuning prompts, context, and project habits
- Anyone who wants useful analytics without giving up control of their logs

## How It Works

Codex Logbook reads local Codex data, prepares dashboard-ready project logs, computes the metrics, and starts a local web dashboard.

By default it looks for:

```text
~/.codex/state_5.sqlite
```

Generated dashboard data is written under:

```text
~/.codex-logbook/codex/projects
```

Use a custom Codex home:

```bash
CODEX_HOME=/path/to/.codex codex-logbook init
```

Use a custom export directory:

```bash
CODEX_LOGBOOK_EXPORT_DIR=/path/to/codex-logbook-projects codex-logbook init
```

## Configuration

```bash
# Change port
codex-logbook config set port 8090

# Disable auto-opening the browser
codex-logbook config set auto_browser false

# Show current configuration
codex-logbook config show
```

Common options:

| Key | Default | Description |
| --- | --- | --- |
| `port` | `8081` | Local dashboard port |
| `host` | `127.0.0.1` | Local dashboard host |
| `auto_browser` | `true` | Open browser automatically |
| `cache_max_projects` | `5` | Max projects kept in memory cache |
| `cache_max_mb_per_project` | `500` | Max memory per project cache |
| `messages_initial_load` | `500` | Initial message rows loaded |
| `max_date_range_days` | `30` | Max selectable chart date range |

See [docs/cli-reference.md](docs/cli-reference.md) for the full CLI reference.

## What To Look For

Use Codex Logbook during weekly reviews or after major project work:

- **High token volume**: Find projects where prompts, context, or repeated work may need cleanup.
- **High cost estimates**: Understand where direct API usage would be expensive.
- **Long step chains**: Spot vague requests that send Codex through unnecessary loops.
- **Low commands per context**: Identify work that quickly fills context windows.
- **High tool-use rate**: Understand which projects require heavy filesystem, terminal, or browser work.
- **Interruption patterns**: Find commands that frequently need manual correction or stopping.

The point is not more charts for the sake of charts. It is to make the next Codex session a little cleaner than the last one.

## Troubleshooting

Port already in use:

```bash
codex-logbook init --port 8090
```

Browser did not open:

```bash
codex-logbook config set auto_browser true
codex-logbook init
```

Codex data not found:

```bash
ls ~/.codex/state_5.sqlite
CODEX_HOME=/path/to/.codex codex-logbook init
```

Show all configuration:

```bash
codex-logbook config show
```

## Development

```bash
git clone https://github.com/Smeet97Kathiria/codex-logbook.git
cd codex-logbook

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest tests/codex_logbook --ignore=tests/codex_logbook/test_performance.py
```

Run the local app:

```bash
codex-logbook init --no-browser
```

Then open:

```text
http://127.0.0.1:8081
```

## Support The Project

If Codex Logbook helps you understand your Codex usage, a star helps more Codex users find a local-first way to make sense of their own logs.

## License

MIT License. See [LICENSE](LICENSE).
