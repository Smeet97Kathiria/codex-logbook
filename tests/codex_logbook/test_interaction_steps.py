#!/usr/bin/env python3
"""Test assistant steps counting."""

import logging

from codex_logbook.core.processor import CodexLogProcessor

logger = logging.getLogger(__name__)

def test_interaction_steps():
    log_dir = "/Users/developer/.codex-logbook/codex/projects/-Users-developer-dev-codex-analysis"
    processor = CodexLogProcessor(log_dir)
    
    # Process logs
    messages, stats = processor.process_logs()
    
    # Find the specific message
    target_timestamp = "2025-06-30T18:49:05.371Z"
    
    for msg in messages:
        if msg.get('timestamp') == target_timestamp and msg.get('type') == 'user':
            logger.info("Found user message:")
            logger.info(f"  Timestamp: {msg['timestamp']}")
            logger.info(f"  interaction_tool_count: {msg.get('interaction_tool_count', 'N/A')}")
            logger.info(f"  interaction_assistant_steps: {msg.get('interaction_assistant_steps', 'N/A')}")
            
            # Count actual assistant messages following this
            assistant_count = 0
            for i, m in enumerate(messages):
                if m == msg:
                    # Count assistant messages after this one
                    j = i + 1
                    while j < len(messages):
                        next_msg = messages[j]
                        if next_msg['type'] == 'user' and not next_msg.get('has_tool_result'):
                            break
                        if next_msg['type'] == 'assistant':
                            assistant_count += 1
                        j += 1
                    break
            
            logger.info(f"  Actual assistant messages in final output: {assistant_count}")
            break

if __name__ == "__main__":
    test_interaction_steps()