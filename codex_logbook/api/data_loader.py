"""
Optimized data loading for the dashboard.
"""


class DataLoader:
    """
    Handles optimized loading of dashboard data.
    """

    @staticmethod
    async def load_dashboard_data(
        processor, memory_cache, cache_service, current_log_path: str
    ) -> tuple[list[dict], dict]:
        """
        Load all data needed for dashboard initialization.

        Returns:
            Tuple of (messages, statistics)
        """
        # Check memory cache first
        memory_result = memory_cache.get(current_log_path)
        if memory_result:
            return memory_result

        # Check file cache
        cached_messages = cache_service.get_cached_messages(current_log_path)
        cached_stats = cache_service.get_cached_stats(current_log_path)

        if cached_messages and cached_stats and not cache_service.has_changes(current_log_path):
            # Store in memory cache for next time
            memory_cache.put(current_log_path, cached_messages, cached_stats)
            return cached_messages, cached_stats

        # Process logs if needed
        messages, statistics = processor.process_logs()

        # Cache the results
        cache_service.save_cached_stats(current_log_path, statistics)
        cache_service.save_cached_messages(current_log_path, messages)
        memory_cache.put(current_log_path, messages, statistics)

        return messages, statistics

    @staticmethod
    def prepare_dashboard_response(messages: list[dict], statistics: dict) -> dict:
        """
        Prepare optimized response for dashboard initialization.

        Instead of sending all messages, send:
        - Full statistics
        - Message summary
        - First page of messages
        """
        # Calculate message summary
        message_summary = {
            "total": len(messages),
            "by_type": {},
            "by_model": {},
            "sessions": set(),
        }

        for msg in messages:
            # Count by type
            msg_type = msg.get("type", "unknown")
            message_summary["by_type"][msg_type] = message_summary["by_type"].get(msg_type, 0) + 1

            # Count by model
            model = msg.get("model", "unknown")
            message_summary["by_model"][model] = message_summary["by_model"].get(model, 0) + 1

            # Collect sessions
            if session := msg.get("session_id"):
                message_summary["sessions"].add(session)

        # Convert set to list for JSON serialization
        message_summary["sessions"] = list(message_summary["sessions"])
        message_summary["session_count"] = len(message_summary["sessions"])

        return {
            "statistics": statistics,
            "messages": messages,  # For now, still include all messages for charts
            "message_summary": message_summary,
            "optimized": True,
        }
