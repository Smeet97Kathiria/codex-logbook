#!/usr/bin/env python3
"""Test the enhanced deduplication and tool counting logic."""

import json
import logging

from codex_logbook.core.processor import CodexLogProcessor

logger = logging.getLogger(__name__)

def test_deduplication():
    # Test with the actual problem logs
    log_dir = "/Users/developer/.codex-logbook/codex/projects/-Users-developer-dev-codex-analysis"
    
    logger.info("Testing enhanced deduplication and tool counting...")
    logger.info(f"Log directory: {log_dir}")
    print()
    
    # Process logs with debug
    processor = CodexLogProcessor(log_dir)
    
    # Add debug to check interaction processing
    import glob
    import os
    files = sorted(glob.glob(os.path.join(log_dir, '*.jsonl')))
    logger.info(f"Found {len(files)} log files")
    for f in files:
        logger.info(f"  - {os.path.basename(f)}")
    print()
    
    messages, stats = processor.process_logs()
    
    # Look for the specific problematic message
    target_content = "for error type distribution chart, the colors of the legends don't match"
    
    logger.info("Searching for duplicate messages...")
    found_messages = []
    
    for msg in messages:
        if msg.get('type') == 'user' and target_content in msg.get('content', '').lower():
            found_messages.append({
                'timestamp': msg.get('timestamp'),
                'session_id': msg.get('session_id'),
                'tool_count': msg.get('interaction_tool_count', 'N/A'),
                'model': msg.get('interaction_model', 'N/A'),
                'content_preview': msg.get('content', '')[:100] + '...'
            })
    
    logger.info(f"\nFound {len(found_messages)} instances of the target message:")
    for i, msg in enumerate(found_messages, 1):
        logger.info(f"\n{i}. Timestamp: {msg['timestamp']}")
        logger.info(f"   Session: {msg['session_id']}")
        logger.info(f"   Tool Count: {msg['tool_count']}")
        logger.info(f"   Model: {msg['model']}")
        logger.info(f"   Content: {msg['content_preview']}")
    
    # Check user command analysis
    logger.info("\n\nUser Command Analysis Summary:")
    user_stats = stats.get('user_interactions', {})
    logger.info(f"Total commands analyzed: {user_stats.get('user_commands_analyzed', 0)}")
    logger.info(f"Commands with tools: {user_stats.get('commands_requiring_tools', 0)}")
    logger.info(f"Total tools used: {user_stats.get('total_tools_used', 0)}")
    
    # Check for commands with high tool counts
    logger.info("\n\nCommands with 10+ tools:")
    command_details = user_stats.get('command_details', [])
    high_tool_commands = [cmd for cmd in command_details if cmd.get('tools_used', 0) >= 10]
    
    for cmd in high_tool_commands[:5]:  # Show first 5
        logger.info(f"\nMessage: {cmd['user_message'][:80]}...")
        logger.info(f"Tools: {cmd['tools_used']}")
        logger.info(f"Model: {cmd['model']}")
        logger.info(f"Session: {cmd['session_id']}")
    
    # Check session continuations
    logger.info("\n\nSession Information:")
    logger.info(f"Total sessions: {stats['overview']['sessions']}")
    logger.info(f"Total messages: {stats['overview']['total_messages']}")
    
    # Verify no duplicates remain
    logger.info("\n\nChecking for remaining duplicates...")
    message_keys = set()
    duplicates = []
    
    for msg in messages:
        if msg.get('type') == 'user' and not msg.get('has_tool_result'):
            key = f"{msg.get('timestamp')}:{msg.get('content', '')[:50]}"
            if key in message_keys:
                duplicates.append(msg)
            message_keys.add(key)
    
    logger.info(f"Remaining duplicates: {len(duplicates)}")
    if duplicates:
        logger.info("Sample duplicate:")
        print(json.dumps(duplicates[0], indent=2)[:500])

if __name__ == "__main__":
    test_deduplication()