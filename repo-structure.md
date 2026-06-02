# Codex Logbook Repository Structure

## Overview
This repository contains Codex Logbook, a dashboard for analyzing Codex logs locally. The project provides performance optimizations, memory caching, comprehensive analytics visualization, and a CLI for easy installation and usage.

## Directory Structure

```
codex-analysis/
├── README.md                    # Main project documentation
├── DEV.md                       # Development guide
├── CODEX.md                     # Project instructions and guidelines
├── repo-structure.md            # This file
├── pyproject.toml               # Python package configuration and single source of version
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── package.json                 # Node.js dependencies for frontend
├── package-lock.json            # Locked Node.js dependencies
├── .env                         # Environment configuration (not in git)
├── .env.example                 # Example environment configuration
├── .eslintrc.json               # JavaScript linting configuration
├── .gitignore                   # Git ignore rules
├── lint.sh                      # Linting script for Python and JavaScript
├── start_local.sh               # Script to start local server
├── run_tests.py                 # Test runner script
├── test-checklist.md            # Testing guidelines
├── test_datepicker.html         # Date picker test page
│
├── .github/                     # GitHub Actions CI/CD
│   └── workflows/
│       ├── build.yml            # Build and test package across platforms
│       ├── lint.yml             # Code quality checks
│       ├── publish.yml          # PyPI publishing workflow
│       └── test.yml             # Unit test runner
│
├── assets/                      # Brand assets
│   ├── lemongrass/              # Lemongrass branding
│   │   ├── favicon.ico
│   │   └── logo.png
│   └── codex_logbook/                 # Codex Logbook branding
│       ├── logo-transparent.png
│       ├── logo-with-text-transparent.png
│       ├── logo-with-text.png
│       ├── codex_logbook_favicon.ico
│       └── codex_logbook_favicon_rounded.ico
│
├── codex_logbook/                     # Main Python package
│   ├── __init__.py              # Package init with version from importlib.metadata
│   ├── __version__.py           # Version string
│   ├── cli.py                   # CLI entry point and commands
│   ├── config.py                # Configuration management system
│   ├── server.py                # FastAPI server with caching
│   ├── share.py                 # Share functionality manager
│   ├── admin.py                 # Admin API endpoints
│   ├── auth.py                  # OAuth authentication
│   │
│   ├── core/                    # Core processing logic
│   │   ├── __init__.py
│   │   ├── constants.py         # Core constants (patterns, limits)
│   │   ├── processor.py         # Log processing and deduplication
│   │   ├── stats.py             # Statistics generation
│   │   └── global_aggregator.py # Cross-project aggregation
│   │
│   ├── api/                     # API endpoints and utilities
│   │   ├── __init__.py
│   │   ├── data.py              # Data formatting utilities
│   │   ├── data_loader.py       # Efficient data loading
│   │   ├── messages.py          # Message handling endpoints
│   │   └── share.py             # Share creation endpoint (Phase 3)
│   │
│   ├── utils/                   # Utility modules
│   │   ├── __init__.py
│   │   ├── cache_warmer.py      # Background cache warming
│   │   ├── local_cache.py       # File-based caching (L2)
│   │   ├── log_finder.py        # Codex log detection
│   │   ├── logging.py           # Logging configuration
│   │   ├── memory_cache.py      # In-memory LRU cache (L1)
│   │   └── pricing.py           # Token pricing calculations
│   │
│   ├── services/                # Service layer
│   │   ├── __init__.py
│   │   └── pricing_service.py   # Dynamic pricing with caching
│   │
│   ├── templates/               # HTML templates
│   │   ├── dashboard.html       # Project analytics dashboard
│   │   └── overview.html        # Global overview page
│   │
│   └── static/                  # Static assets
│       ├── favicon.ico          # Default favicon
│       ├── images/              # Static images
│       │   └── logo.png
│       ├── css/                 # Stylesheets
│       │   ├── dashboard.css    # Main dashboard styles
│       │   ├── date-range-picker.css  # Date picker component styles
│       │   └── project-selector.css    # Project dropdown styles
│       └── js/                  # JavaScript modules
│           ├── chart-code-examples.js  # Chart templates
│           ├── charts.js        # Chart initialization
│           ├── commands-tab.js  # Commands tab functionality
│           ├── constants.js     # Shared constants
│           ├── date-range-picker.js
│           ├── dynamic-interval-chart-builder.js
│           ├── export.js        # Export functionality
│           ├── jsonl-viewer.js  # JSONL file viewer
│           ├── memory-monitor.js # Browser memory tracking
│           ├── messages-tab.js  # Messages tab functionality
│           ├── overview.js      # Overview page logic
│           ├── pricing.js       # Pricing calculations
│           ├── project-detector.js # Project URL handling
│           ├── share-modal.js   # Share modal functionality (Phase 3)
│           ├── stats.js         # Statistics calculations
│           ├── stats-cards.js   # Statistics card display module
│           └── utils.js         # Utility functions
│
├── docs/                        # Documentation
│   ├── cli-reference.md         # Complete CLI command reference
│   ├── codex-logs-structure.md # Log format specification
│   ├── COST_CALCULATION_PLAN.md
│   ├── LOCAL_MODE_EXPORT_PLAN.md
│   ├── LOG_DEDUPLICATION_PLAN.md
│   ├── logs-processing-design.md
│   ├── codex_logbook-distribution-plan.md  # Phase 2 & 3 implementation plan
│   ├── assistant-step-time.md   # Why timing was removed
│   ├── dashboard-html-structure.md
│   ├── global-stats.md          # Global overview documentation
│   ├── linting.md               # Linting issues and fixes
│   ├── memory-and-latency-optimization.md
│   ├── model-pricing.md
│   ├── optimization-summary.md
│   ├── performance-profiling-results.md
│   ├── processing-speedup.md
│   ├── processor-structure.md   # Processor documentation
│   ├── specs.md                 # Technical specifications (Phase 1-3)
│   ├── stats-structure.md       # Statistics documentation
│   ├── summary_datepicker.md
│   ├── tests.md                 # Testing documentation
│   ├── user_tool_analysis.md    # Tool usage insights
│   ├── code-quality-analysis.md # Code quality improvement opportunities
│   └── refactoring-example.md   # Example refactoring patterns
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── baseline_results.json    # Expected test results
│   ├── baseline_phase2.json     # Phase 2 baselines
│   ├── test_cli.py              # CLI command tests
│   ├── test_deduplication.py    # Deduplication tests
│   ├── test_interaction_steps.py
│   ├── test_performance.py      # Performance benchmarks
│   ├── test_processor_data_verification.py
│   ├── test_processor_optimization_correctness.py
│   ├── test_server.py           # API endpoint tests
│   ├── test_share.py            # Share functionality tests
│   ├── test_admin.py            # Admin module tests
│   │
│   ├── core/                    # Core module tests
│   │   ├── __init__.py
│   │   ├── test_global_aggregator.py
│   │   ├── test_processor.py
│   │   └── test_stats.py
│   │
│   ├── utils/                   # Utility tests
│   │   ├── __init__.py
│   │   ├── test_log_finder.py
│   │   └── test_memory_cache.py
│   │
│   └── mock-data/               # Test data
│       ├── -Users-developer-dev-demo-project/
│       │   ├── *.jsonl          # Sample log files
│       │   └── .continuation_cache.json
│       ├── -Users-developer-dev-large-project/
│       │   ├── *.jsonl          # Sample log files
│       │   └── .continuation_cache.json
│       └── pricing.json         # Test pricing data
│
├── codex-logbook-site/                # Static site for sharing (Phase 3)
│   ├── README.md                # Site documentation
│   ├── build.py                 # Build script to bundle dashboard assets
│   ├── index.html               # Landing page with gallery
│   ├── share-template.html      # Template for shared dashboards
│   ├── share.html               # Generated share page (built by build.py)
│   ├── admin.html               # Admin dashboard
│   ├── package.json             # Node configuration
│   ├── functions/               # Cloudflare Pages Functions
│   │   └── share/
│   │       └── [[id]].js        # Dynamic share handler (fetches from R2)
│   └── static/                  # Site assets
│       ├── css/
│       │   ├── style.css        # Landing page styles
│       │   ├── gallery.css      # Gallery styles
│       │   └── admin.css        # Admin dashboard styles
│       └── js/
│           ├── gallery.js       # Gallery functionality
│           ├── share-viewer.js  # Renders shared dashboards with Chart.js
│           └── admin.js         # Admin dashboard functionality
│
├── scripts/                     # Utility scripts
│   └── start_local.py           # Alternative server starter
│
├── fake-r2/                     # Local R2 storage mock (Phase 3 development)
│   ├── gallery-index.json       # Public shares index
│   ├── shares-log.jsonl         # Share creation logs for analytics
│   └── *.json                   # Shared dashboard data files
│
├── graphs/                      # Generated analytics (not in git)
│   └── {project-name}/          # Per-project analytics
│       ├── analytics_report.pdf
│       ├── overview_statistics.png
│       └── charts/              # Individual chart PNGs
│
├── data/                        # Data directory placeholder
│
├── Analysis scripts (root)      # Various analysis utilities
│   ├── analyze_command_completion_times.py
│   ├── analyze_parallel_tools.py
│   ├── analyze_response_times.py
│   ├── analyze_streaming_messages.py
│   ├── analyze_tool_step_ratio.py
│   ├── extract_other_errors.py
│   ├── find-codex-logs.sh
│   ├── profile_backend.py
│   ├── profile_workflow.py
│   ├── test_complexity_data.py
│   ├── test_extraction.py
│   ├── test_merge_debug.py
│   ├── test_message_ids.py
│   ├── test_single_pass_dedup.py
│   ├── test_specific_interaction.py
│   └── test_tool_names.py
│
└── Generated/cached files (not in git)
    ├── .mypy_cache/             # MyPy type checking cache
    ├── .pytest_cache/           # Pytest cache
    ├── .ruff_cache/             # Ruff linting cache
    ├── __pycache__/             # Python bytecode
    ├── htmlcov/                 # Coverage HTML reports
    ├── node_modules/            # Node.js dependencies
    ├── venv/                    # Python virtual environment
    ├── dist/                    # Built packages
    ├── build/                   # Build artifacts
    ├── server.log               # Server logs
    └── *.egg-info/              # Package metadata
```

## Key Features

### Multi-Layered Caching
- **L1 Cache**: In-memory LRU cache with configurable size limits
- **L2 Cache**: File-based persistent cache
- **Cache Warming**: Background preloading for instant switching

### Performance Optimizations
- Processing rate: ~150,000 messages/second
- Initial load: <500ms for overview page
- Smart refresh: ~5ms when no changes detected
- Progressive loading: 50 → 1000 → all messages

### CLI Commands
- `codex-logbook init`: Start the dashboard server
- `codex-logbook config`: Manage configuration
- `codex-logbook clear-cache`: Clear all caches
- `codex-logbook version`: Show version info
- `codex-logbook help`: Show help information

### API Endpoints
- `/`: Global overview page
- `/project/{name}`: Project-specific dashboard
- `/api/projects`: List all projects
- `/api/global-stats`: Aggregated statistics
- `/api/dashboard-data`: Project data (optimized)
- `/api/messages`: Progressive message loading
- `/api/refresh`: Smart refresh endpoint
- `/api/cache/status`: Cache performance metrics
- `/api/share/create`: Create shareable link (Phase 3)

## Recent Changes

### 2025-01-07
- Updated Phase 3 plan for shareable dashboard features
- Removed auto-expiration in favor of future user-controlled deletion
- Clarified data export approach (raw data, not PNG images)
- Fixed date range picker responsive layout
- Changed share ID length to 16 characters
- Replaced setup.py with modern pyproject.toml approach
- Set version to 0.1.0 with single source of truth

### 2025-01-06
- Completed package renaming from codex_logbook to codex_logbook
- Published to TestPyPI for testing
- Added comprehensive CLI with configuration management
- Created installation and troubleshooting documentation
- Set up GitHub Actions for CI/CD

### 2025-01-05
- Added analytics export functionality (PDF, PNG, CSV)
- Implemented chart generation for various metrics
- Added command completion time analysis

### 2025-01-03
- Implemented global overview dashboard
- Added project-specific URLs
- Removed timing features (inherently inaccurate)
- Refactored statistics into separate module

## Configuration

Environment variables in `.env`:
- `CACHE_MAX_PROJECTS`: Maximum projects in memory cache
- `CACHE_MAX_MB_PER_PROJECT`: Memory limit per project
- `CACHE_WARMING_ENABLED`: Enable background cache warming
- `ENABLE_MEMORY_MONITOR`: Enable browser memory tracking
- `ENV`: Environment (DEV/PROD)

## Development

### Setup
```bash
pip install -e .
pip install -r requirements-dev.txt
```

### Testing
```bash
pytest                          # Run all tests
./lint.sh                       # Run linters
python run_tests.py             # Alternative test runner
```

### Linting
- **Python**: Ruff (linting + formatting) and MyPy (type checking)
- **JavaScript**: ESLint (currently disabled in CI)

## Project Status

### Phase 1: ✅ Complete
- Global overview dashboard with project statistics
- Project-specific dashboards with detailed analytics
- Multi-layered caching for performance

### Phase 2: ✅ Complete (Ready for PyPI)
- CLI tool with configuration management
- Package renamed to `codex_logbook`
- TestPyPI testing successful
- Awaiting PyPI account setup for publishing

### Phase 3: 📋 In Planning
- Shareable dashboard feature
- Static site hosted on Cloudflare Pages
- Selective data export (stats, charts, optional commands)
- Public gallery for shared projects

## Notes

- Windows support is not currently available
- Performance tests are disabled in CI due to hardware variability
- Version 0.1.0 ready for initial release
