import asyncio
import logging

from codex_logbook.config import Config
from codex_logbook.core.processor import CodexLogProcessor
from codex_logbook.utils.log_finder import get_all_projects_with_metadata

logger = logging.getLogger(__name__)

# Get config instance
_config = Config()
cache_warm_on_startup = _config.get("cache_warm_on_startup")


def _process_project_for_cache(cache_service, memory_cache, log_path: str, force: bool = True) -> bool:
    processor = CodexLogProcessor(log_path)
    messages, stats = processor.process_logs()

    cache_service.save_cached_stats(log_path, stats)
    cache_service.save_cached_messages(log_path, messages)
    return memory_cache.put(log_path, messages, stats, force=force)


# Background tasks
async def warm_recent_projects(
    cache_service, memory_cache, current_log_path, exclude_current: bool = False, limit: int = None
):
    """Preload recent projects into memory cache in background"""
    if limit is None:
        limit = cache_warm_on_startup

    try:
        # Get recent projects
        log_dirs = []
        for project in get_all_projects_with_metadata():
            log_path = project["log_path"]
            if exclude_current and log_path == current_log_path:
                continue
            log_dirs.append((log_path, project["last_modified"], project["dir_name"]))

        # Sort by most recent JSONL modification time (most recent first)
        log_dirs.sort(key=lambda x: x[1], reverse=True)

        # Take only the most recent projects
        recent_dirs = log_dirs[:limit]

        logger.debug(f"Starting to warm {len(recent_dirs)} recent projects")

        for log_path, _, log_name in recent_dirs:
            # Skip if already in memory cache
            if memory_cache.get(log_path):
                logger.info(f"{log_name} already in memory cache")
                continue

            # Yield to other tasks
            await asyncio.sleep(0.1)

            try:
                if await asyncio.to_thread(_process_project_for_cache, cache_service, memory_cache, log_path, True):
                    logger.debug(f"Successfully warmed {log_name}")
                else:
                    logger.debug(f"Failed to cache {log_name} (too large)")

            except Exception as e:
                logger.info(f"Error processing {log_name}: {e}")

            # Longer delay between projects to avoid hogging resources
            await asyncio.sleep(0.5)

        logger.debug(f"Completed warming {len(recent_dirs)} projects")

    except Exception as e:
        logger.info(f"Error in warm_recent_projects: {e}")
