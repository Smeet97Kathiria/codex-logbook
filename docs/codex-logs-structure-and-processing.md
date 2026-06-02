# Codex Logs Structure and Processing Documentation

This document comprehensively describes Codex log files (JSONL format), their structure, and how Codex Logbook processes them to generate analytics while handling complex edge cases.

## Table of Contents
1. [Log File Structure](#log-file-structure)
2. [Entry Types and Fields](#entry-types-and-fields)
3. [Message Formats](#message-formats)
4. [Tool Usage](#tool-usage)
5. [Special Cases](#special-cases)
6. [Processing Strategy](#processing-strategy)
7. [Deduplication and Tool Counting](#deduplication-and-tool-counting)
8. [Performance and Caching](#performance-and-caching)
9. [Known Issues and Solutions](#known-issues-and-solutions)

## Log File Structure

### File Location
```
~/.codex-logbook/codex/projects/{project-path-hash}/{session-id}.jsonl
```

Example:
```
/Users/developer/.codex-logbook/codex/projects/-Users-example-user-dev-macro-logbook-macro-logbook-codex/08fce8c2-8453-42da-a52c-e03472c24e0f.jsonl
```

### Important: Multiple Sessions Per File
While JSONL files are named after a primary session ID, they can contain log entries from multiple sessions:

1. **Conversation Continuation**: When a conversation is continued after compaction or restart
2. **Cross-Session References**: When Codex references work from another session
3. **Session Merging**: When multiple related sessions are logged together

**Best Practice**: Always use the filename (without .jsonl) as the authoritative session ID for the file.

## Entry Types and Fields

### Entry Types
- `summary` - Session or conversation summary
- `user` - User messages (includes tool results)
- `assistant` - Codex's responses

**Important:** The root `type` field indicates the log entry type, NOT necessarily the message role.

### Common Fields

#### All Entries
- `type` (string): Type of the entry
- `timestamp` (ISO 8601): When the entry was created
- `uuid` (string): Unique identifier for this entry

#### User/Assistant Entries
- `sessionId` (string): Session identifier
- `parentUuid` (string|null): UUID of the parent message
- `isSidechain` (boolean): Whether this is a side conversation (e.g., Task tool)
- `userType` (string): Type of user (e.g., "external")
- `cwd` (string): Current working directory
- `version` (string): Codex version
- `message` (object): The actual message content

#### Assistant-Specific Fields
- `requestId` (string): API request identifier
- `message.id` (string): Unique message ID (important for streaming)

#### User-Specific Fields
- `toolUseResult` (object|string): Detailed tool execution results
- `isCompactSummary` (boolean): True for conversation summaries

## Message Formats

### User Messages
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "User's message text"
      },
      {
        "type": "tool_result",
        "tool_use_id": "tool_id",
        "content": "Tool execution result"
      }
    ]
  }
}
```

### Assistant Messages
```json
{
  "type": "assistant",
  "message": {
    "id": "msg_id",
    "type": "message",
    "role": "assistant",
    "model": "codex-opus-4-20250514",
    "content": [
      {
        "type": "text",
        "text": "Codex's response text"
      },
      {
        "type": "tool_use",
        "id": "toolu_xxxxx",
        "name": "ToolName",
        "input": {
          "parameter": "value"
        }
      }
    ],
    "stop_reason": "tool_use",
    "usage": {
      "input_tokens": 1234,
      "output_tokens": 567,
      "cache_creation_input_tokens": 890,
      "cache_read_input_tokens": 123
    }
  }
}
```

### Summary Entries
```json
{
  "type": "summary",
  "summary": "Brief description of the conversation",
  "leafUuid": "uuid-of-last-message"
}
```

## Tool Usage

### Common Tools
- File Operations: `Read`, `Write`, `Edit`, `MultiEdit`
- System: `Bash`, `Grep`, `Glob`, `LS`
- Task Management: `TodoWrite`, `TodoRead`
- Special: `Task` (launches sub-agents), `WebFetch`, `WebSearch`
- Jupyter: `NotebookRead`, `NotebookEdit`

### Tool Results
Tool results appear in subsequent user messages:
```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_xxxxx",
  "content": "Result of tool execution",
  "is_error": true  // If tool execution failed
}
```

### Task Tool Limitations
**Critical**: Task tool operations are NOT individually logged:
- Only the Task invocation and final result appear in logs
- Internal tool operations by sub-agents are invisible
- Token usage by sub-agents is NOT tracked
- This causes apparent "missing" tool counts in analytics

## Special Cases

### Streaming Responses
Codex logs streaming responses as multiple entries with the same message ID:

```json
// Entry 1: Text response
{
  "type": "assistant",
  "message": {
    "id": "msg_01Y9yWFraRY5ptb3Bqbvpmqx",
    "content": [{"type": "text", "text": "I'll implement..."}]
  }
}

// Entry 2: Tool use (same message ID)
{
  "type": "assistant", 
  "message": {
    "id": "msg_01Y9yWFraRY5ptb3Bqbvpmqx",
    "content": [{"type": "tool_use", "name": "Write", ...}]
  }
}
```

### Conversation Compaction
When conversations approach context limits, Codex creates comprehensive summaries:

```json
{
  "type": "user",
  "isCompactSummary": true,
  "message": {
    "role": "user",
    "content": [{
      "type": "text",
      "text": "This session is being continued from a previous conversation..."
    }]
  }
}
```

### Error Types

#### User Rejection (Before Execution)
```json
{
  "type": "tool_result",
  "content": "The user doesn't want to proceed with this tool use...",
  "is_error": true
}
```

#### User Interruption (During Execution)
Appears as both error AND user message:
```json
// As error
{
  "type": "tool_result",
  "content": "[Request interrupted by user for tool use]",
  "is_error": true
}
// As user message
{
  "type": "user",
  "message": {
    "content": [{"text": "[Request interrupted by user for tool use]no, don't..."}]
  }
}
```

## Processing Strategy

### Overview
Codex Logbook processes logs to handle:
1. Streaming response merging
2. Message deduplication
3. Proper type classification
4. Tool count reconciliation
5. Timezone conversion
6. Performance optimization

### Message Type Classification
```python
# Base type from root field
base_type = msg['type']

# Special cases
if msg.get('isSidechain') and base_type == 'user':
    type = 'task'
elif msg.get('isCompactSummary'):
    type = 'compact_summary'
elif base_type == 'summary':
    type = 'summary'
```

### Timezone Handling
All timestamps are stored in UTC but displayed in user's local timezone:

1. Frontend detects timezone offset: `new Date().getTimezoneOffset()`
2. Backend converts UTC to local time for grouping
3. Charts display dates in user's local timezone

## Deduplication and Tool Counting

### The Problem
When Codex crashes and restarts with `--continue`:
- Duplicate messages appear in multiple files
- Same message shows inconsistent tool counts
- Incomplete assistant responses
- Missing tool execution logs

### Solution: Interaction-Based Processing

Instead of processing individual messages, group into complete interactions:

```python
class Interaction:
    user_message: Dict
    assistant_messages: List[Dict]
    tools_used: List[Dict]
    is_complete: bool
    session_id: str
    interaction_id: str  # Hash of user content + timestamp
```

### Deduplication Algorithm

#### 1. Session Continuation Detection
```python
def _detect_session_continuations(files):
    # Look for isCompactSummary in first messages
    # Check for "continue" commands
    # Map sessions to their predecessors
```

#### 2. Interaction Grouping
```python
def _group_into_interactions(messages):
    # Group user message + following assistant messages
    # Handle split interactions across files
    # Track tool executions
```

#### 3. Intelligent Merging
```python
def _merge_duplicate_interactions(duplicates):
    # Score interactions by completeness
    # Prefer interactions with:
    #   - Complete responses
    #   - More tools
    #   - Output tokens
    #   - Later sessions
```

#### 4. Tool Count Reconciliation
```python
def _reconcile_tool_counts(interaction):
    # Count from assistant messages
    # Verify against tool results
    # Handle Task tool (counts as 1)
    # Infer from content if needed
```

### Edge Cases Handled

1. **Split Interactions**: User message in file A, assistant response in file B
2. **Incomplete Tool Executions**: Crash during tool execution
3. **Compact Summary Continuations**: Sessions starting with summaries
4. **Missing Tool Logs**: Tools used but not logged
5. **Streaming Response Merging**: Multiple entries with same message ID
6. **Task Tool Sidechains**: Sub-agent operations not logged

## Performance and Caching

### Backend Optimization
1. **Streaming Parser**: Line-by-line processing for large files
2. **Backend Chart Calculation**: All aggregation done server-side
3. **Pre-computed Statistics**: Charts use cached calculations

### Caching Strategy

#### Two-Tier Cache System
1. **Memory Cache (L1)**: Fast in-memory storage
   - LRU eviction
   - Configurable size limits
   - ~74,000x speedup for retrieval

2. **File Cache (L2)**: Persistent disk storage
   - JSON format
   - Change detection via file stats
   - ~2.4x speedup vs reprocessing

### Data Refresh
Smart change detection minimizes unnecessary reprocessing:

1. Check file metadata (size + mtime)
2. If no changes: Keep cache (<5ms)
3. If changes: Invalidate and reprocess
4. Auto-reload UI after update

### Performance Benchmarks
- Processing: ~27,000 messages/second
- Memory: ~36KB per message
- Cache hit: <5ms response time
- Full refresh: ~1.6s for 124MB project

## Known Issues and Solutions

### Issue 1: Duplicate Commands in Table
**Cause**: Same user message in multiple files after crash/continue
**Solution**: Interaction-based deduplication with content hashing

### Issue 2: Wrong Tool Counts
**Cause**: Incomplete logging, Task tool limitations, streaming issues
**Solution**: Tool count reconciliation across all interaction versions

### Issue 3: Missing Model Names
**Cause**: Incomplete assistant messages from crashes
**Solution**: Preserve model info during interaction merging

### Issue 4: Overview Refresh Intermittent
**Status**: Documented in TODO
**Workaround**: Refresh individual project dashboards first

## Success Metrics

1. **Accuracy**: No duplicate messages, correct type classification
2. **Performance**: Efficient processing with caching
3. **Completeness**: All tools counted accurately
4. **Timezone Support**: Correct local time display
5. **Reliability**: Graceful handling of crashes and continuations