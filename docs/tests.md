# Codex Logbook Test Documentation

## Overview
This document describes the test suite for Codex Logbook, including unit tests, integration tests, and performance benchmarks.

## Test Structure

The test directory structure mirrors the `codex_logbook` module structure for better organization:

```
tests/
├── core/                    # Core functionality tests
│   ├── test_processor.py    # Log processing tests (23 tests)
│   ├── test_stats.py        # Statistics extraction tests (13 tests)
│   └── test_global_aggregator.py  # Cross-project aggregation (7 tests)
├── utils/                   # Utility tests
│   ├── test_memory_cache.py     # Memory cache tests (9 tests)
│   └── test_log_finder.py       # Log discovery tests (6 tests)
├── test_cli.py              # CLI command tests (19 tests)
├── test_server.py           # API endpoint tests (18 tests)
├── test_performance.py      # Performance benchmarks (8 tests)
├── test_processor_data_verification.py  # Data validation tests (13 tests)
├── test_processor_optimization_correctness.py  # Optimization tests (6 tests)
├── test_deduplication.py    # Message deduplication tests
├── test_interaction_steps.py # User interaction tests
└── data/                    # Test data files
    ├── *.jsonl              # Sample Codex log files
    ├── baseline_results.json     # Expected results for regression testing
    └── baseline_phase2.json      # Phase 2 optimization baseline

Total: 126 tests (plus 2 skipped CLI tests)
```

### What Each Test Suite Covers

#### Core Tests (`tests/core/`)

**test_processor.py** (23 tests):
- Message extraction from JSONL logs
- Token counting accuracy
- Deduplication of messages
- Streaming message handling
- Error detection and categorization
- Session management
- Tool usage tracking
- User interaction patterns

**test_stats.py** (13 tests):
- Lightweight statistics extraction
- Daily/hourly activity aggregation
- Model usage tracking
- Cost calculations
- Cache functionality
- Incremental processing

**test_global_aggregator.py** (7 tests):
- Cross-project statistics
- Project listing and sorting
- Aggregate metrics calculation
- Overview page data generation

#### Utility Tests (`tests/utils/`)

**test_memory_cache.py** (9 tests):
- LRU cache eviction
- Memory limit enforcement
- Cache hit/miss tracking
- Project prioritization
- Concurrent access safety

**test_log_finder.py** (6 tests):
- Codex log directory discovery
- Project path to log path conversion
- Cross-platform path handling
- Log file filtering

#### Integration Tests

**test_cli.py** (19 tests):
- CLI command parsing
- Configuration management
- Config file persistence
- Environment variable handling
- Command output formatting
- Note: 2 tests skipped (init command tests require full server import)

**test_server.py** (18 tests):
- API endpoint functionality
- FastAPI integration
- Request/response validation
- Error handling
- CORS configuration

#### Performance Tests

**test_performance.py** (8 tests):
- Processing speed benchmarks (~12,000 messages/second)
- Memory usage profiling
- Scalability testing
- Cache performance (L1 and L2)
- Parallel processing efficiency
- API response time measurements

#### Data Verification Tests

**test_processor_data_verification.py** (13 tests):
- Validates against known baseline data
- Ensures consistent output
- Regression testing for processing logic
- Edge case handling

**test_processor_optimization_correctness.py** (6 tests):
- Verifies optimizations don't break functionality
- Compares optimized vs baseline results
- Ensures data integrity

### Test Data
- `tests/mock-data/` - Contains sample JSONL files from real Codex sessions
- `tests/baseline_results.json` - Expected results for regression testing
- `tests/baseline_phase2.json` - Phase 2 optimization baseline results

## Running Tests

### All Tests
```bash
python run_tests.py
```

### Specific Test Modules
```bash
python run_tests.py -m processor
python run_tests.py -m stats
python run_tests.py -m performance
```

### With Coverage
```bash
python run_tests.py -c
```

### Performance Tests Only
```bash
python run_tests.py -p
```

## Performance Test Updates (2025-01-03)

### Background
The `test_performance.py` file was updated to reflect the actual production code architecture. Previously, it was testing the unused `stats.py` module alongside the main processor. The tests have been updated to match the real implementation.

### Changes Made

#### 1. Updated Imports
- **Removed**: `from codex_logbook.core.stats import extract_codex_statistics`
- **Added**: 
  - `from codex_logbook.utils.memory_cache import MemoryCache`
  - `from codex_logbook.utils.local_cache import LocalCacheService`

#### 2. Updated test_full_processing_time()
- Removed the separate "stats extraction" step that used `extract_codex_statistics`
- Updated to reflect that `processor.process_logs()` returns both messages and statistics
- Changed dashboard data preparation to match actual `server.py` implementation:
  - Added `chart_messages` with content field stripped for efficiency
  - Added `messages_page` with pagination (first 50 messages)
  - Added `message_count` field
- Added `_strip_content()` helper method to remove content field from messages

#### 3. Replaced test_stats_extraction_performance()
- **Removed**: Test for the unused `extract_codex_statistics` function
- **Replaced with**: `test_memory_cache_performance()` that tests the actual memory cache
- Tests cache put/get operations
- Verifies sub-millisecond retrieval times
- Measures speedup factor

#### 4. Added test_file_cache_performance()
- New test for the file-based cache (L2 cache) that's part of the actual architecture
- Tests `LocalCacheService` save/load operations
- Measures performance improvements over raw processing
- Verifies cache integrity

#### 5. Updated test_dashboard_api_response_time()
- Removed references to `light_stats` from `extract_codex_statistics`
- Updated endpoints to match actual `server.py` API endpoints:
  - `/api/stats` - Returns just statistics
  - `/api/messages` - Returns paginated messages
  - `/api/dashboard-data` - Returns the full dashboard payload
- Added memory cache simulation to match production behavior
- Improved error handling for JSON serialization

### Rationale
These changes align the performance tests with the actual production architecture where:
- All processing and statistics generation happens in `processor.py`
- The `stats.py` module is not used anywhere in production
- Memory and file caching are key performance features
- The dashboard uses specific data structures for optimization

The updated tests now accurately measure the performance of code paths that are actually used in production.

## Performance Benchmarks

### Expected Performance (Phase 2 Optimized)
- **Processing Rate**: >10,000 messages/second (typical: 25,000-27,000)
- **Large Datasets**: >15 files/second
- **Memory Cache Hit**: <1ms retrieval time
- **File Cache Load**: <500ms for large projects
- **API Response Time**: <100ms for all endpoints

### Memory Usage
- **Per Message**: <0.5MB
- **Total for Large Project**: <500MB
- **Cache Size Limits**: 
  - 5 projects in memory (configurable)
  - 500MB per project (configurable)

## Test Coverage

### Core Functionality
- Message extraction and parsing
- Streaming message deduplication
- Session continuation handling
- Tool usage reconciliation
- Error categorization
- Cost calculation

### Performance
- End-to-end processing time
- Memory efficiency
- Cache performance (L1 and L2)
- API response times
- Scalability projections

### Data Integrity
- Deduplication accuracy
- Token counting correctness
- Statistics generation
- Message ordering
- Tool count accuracy

## Profiling Scripts Updates (2025-01-03)

### Background
The profiling scripts `profile_backend.py` and `profile_workflow.py` were updated to remove references to the unused `stats.py` module and align with the actual production architecture.

### Changes to profile_backend.py

#### 1. Updated Imports
- **Removed**: `from codex_logbook.core.stats import extract_codex_statistics`
- **Added**: 
  - `from codex_logbook.utils.memory_cache import MemoryCache`
  - `from codex_logbook.utils.local_cache import LocalCacheService`

#### 2. Replaced profile_stats_extraction()
- **Removed**: Function that profiled the unused `extract_codex_statistics`
- **Replaced with**: `profile_cache_performance()` that profiles:
  - Memory cache put/get operations
  - File cache save/load operations
  - Cache size and speedup metrics

### Changes to profile_workflow.py

#### 1. Updated Imports
- Same as profile_backend.py - removed stats module, added cache modules

#### 2. Updated profile_backend_processing()
- Removed Phase 3 that called `extract_codex_statistics`
- Replaced with cache storage phase that simulates real workflow
- Updated return value to remove `light_stats`

#### 3. Updated API Endpoints
- Changed `/api/messages` to `/api/dashboard-data` (the optimized endpoint)
- Added test for paginated messages endpoint `/api/messages?page=1&per_page=50`
- Better reflects actual API structure

### Profiling Script Usage

#### Backend Profiling
```bash
python profile_backend.py
```
Profiles:
- Detailed phase-by-phase processing breakdown
- Memory usage and efficiency
- Cache performance (memory and file)
- Bottleneck identification

#### Workflow Profiling
```bash
python profile_workflow.py
```
Profiles:
- End-to-end workflow from data loading to API response
- Backend processing performance
- API endpoint response times and sizes
- Memory usage projections
- Generates timestamped JSON report