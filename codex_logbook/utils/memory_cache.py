"""
Memory cache implementation for Codex Logbook.
Provides fast in-memory caching for recently accessed projects.
"""

import logging
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)


class MemoryCache:
    """
    LRU memory cache for project data with access-time protection.

    Stores the last N projects in memory for instant access.
    Includes size limits and automatic eviction with protection for recently-accessed projects.

    Features:
    - LRU eviction based on access patterns
    - Protection window for recently-accessed projects (5 minutes)
    - Size limits per project
    - Background processes cannot evict protected projects
    """

    def __init__(self, max_projects: int = 5, max_mb_per_project: int = 500):
        """
        Initialize memory cache.

        Args:
            max_projects: Maximum number of projects to keep in memory
            max_mb_per_project: Maximum size in MB for a single project
        """
        self.cache: OrderedDict[str, tuple[list[dict], dict, float, float]] = OrderedDict()
        self.max_projects = max_projects
        self.max_mb_per_project = max_mb_per_project
        self.max_bytes_per_project = max_mb_per_project * 1024 * 1024

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.size_rejections = 0

        # Track access times separately for protection
        # This prevents background processes from evicting recently-used projects
        self.last_access: dict[str, float] = {}

    def get(self, project_path: str) -> tuple[list[dict], dict] | None:
        """
        Get project data from memory cache.

        Args:
            project_path: Path to the project log directory

        Returns:
            Tuple of (messages, statistics) if found, None otherwise
        """
        start = time.time()

        if project_path in self.cache:
            # Move to end (LRU) - most recently used
            messages, stats, timestamp, _ = self.cache.pop(project_path)
            self.cache[project_path] = (messages, stats, timestamp, time.time())

            # Track last access time for protection against background eviction
            self.last_access[project_path] = time.time()

            self.hits += 1
            duration_ms = (time.time() - start) * 1000
            logger.debug(f"[Cache] Memory hit for {project_path} ({duration_ms:.1f}ms)")

            return messages, stats

        self.misses += 1
        logger.debug(f"[Cache] Memory miss for {project_path}")
        return None

    def put(self, project_path: str, messages: list[dict], stats: dict, force: bool = False) -> bool:
        """
        Store project data in memory cache.

        Args:
            project_path: Path to the project log directory
            messages: List of message dictionaries
            stats: Statistics dictionary
            force: If True, will evict even recently-accessed projects

        Returns:
            True if cached successfully, False if too large or protected project would be evicted
        """
        # Check size before caching
        size_estimate = self._estimate_size(messages, stats)

        if size_estimate > self.max_bytes_per_project:
            self.size_rejections += 1
            logger.warning(
                f"[Cache] Skipping {project_path} - too large "
                f"({size_estimate / 1024 / 1024:.1f}MB > {self.max_mb_per_project}MB limit)"
            )
            return False

        # Handle cache capacity limits
        if len(self.cache) >= self.max_projects:
            # Find least recently accessed project that can be evicted
            eviction_candidate = None
            oldest_access_time = float("inf")

            # Projects accessed in the last 5 minutes are protected from background eviction
            # This ensures actively-used projects stay in memory even during background processing
            protection_window = 300  # 5 minutes
            current_time = time.time()

            for path in self.cache:
                access_time = self.last_access.get(path, 0)
                age = current_time - access_time

                # Skip recently accessed projects unless force=True
                # force=True is used only during initial cache warming
                if not force and age < protection_window:
                    continue

                if access_time < oldest_access_time:
                    oldest_access_time = access_time
                    eviction_candidate = path

            if eviction_candidate:
                # Found an old project that can be safely evicted
                self.cache.pop(eviction_candidate)
                self.last_access.pop(eviction_candidate, None)
                self.evictions += 1
                logger.debug(f"[Cache] Evicted {eviction_candidate} (LRU)")
            elif not force:
                # All projects are protected - background process should skip this project
                logger.debug(f"[Cache] Cannot evict - all {len(self.cache)} projects accessed recently")
                return False
            else:
                # Force eviction of least recently used (only during initial warming)
                evicted_path, _ = self.cache.popitem(last=False)
                self.last_access.pop(evicted_path, None)
                self.evictions += 1
                logger.debug(f"[Cache] Force evicted {evicted_path} (LRU)")

        # Add to cache
        current_time = time.time()
        self.cache[project_path] = (messages, stats, current_time, current_time)
        self.last_access[project_path] = current_time
        logger.debug(f"[Cache] Stored {project_path} ({size_estimate / 1024 / 1024:.1f}MB, {len(messages)} messages)")

        return True

    def invalidate(self, project_path: str) -> bool:
        """
        Remove a project from the cache.

        Args:
            project_path: Path to the project log directory

        Returns:
            True if removed, False if not in cache
        """
        if project_path in self.cache:
            del self.cache[project_path]
            self.last_access.pop(project_path, None)
            logger.debug(f"[Cache] Invalidated {project_path}")
            return True
        return False

    def clear(self):
        """Clear all cached data."""
        count = len(self.cache)
        self.cache.clear()
        self.last_access.clear()
        logger.debug(f"[Cache] Cleared {count} projects from memory")

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        total_size = sum(self._estimate_size(msgs, stats) for msgs, stats, _, _ in self.cache.values())

        hit_rate = 0.0
        if self.hits + self.misses > 0:
            hit_rate = (self.hits / (self.hits + self.misses)) * 100

        return {
            "projects_cached": len(self.cache),
            "max_projects": self.max_projects,
            "total_size_mb": total_size / 1024 / 1024,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "size_rejections": self.size_rejections,
            "cache_keys": list(self.cache.keys()),
        }

    def get_project_info(self, project_path: str) -> dict[str, Any] | None:
        """
        Get information about a cached project.

        Args:
            project_path: Path to the project log directory

        Returns:
            Project info if cached, None otherwise
        """
        if project_path not in self.cache:
            return None

        messages, stats, timestamp, last_accessed = self.cache[project_path]
        size = self._estimate_size(messages, stats)

        return {
            "path": project_path,
            "message_count": len(messages),
            "size_mb": size / 1024 / 1024,
            "cached_at": timestamp,
            "age_seconds": time.time() - timestamp,
            "last_accessed": last_accessed,
            "last_access_age_seconds": time.time() - self.last_access.get(project_path, last_accessed),
        }

    def _estimate_size(self, messages: list[dict], stats: dict) -> int:
        """
        Estimate memory size of data.

        This is an approximation - actual memory usage may vary.

        Args:
            messages: List of message dictionaries
            stats: Statistics dictionary

        Returns:
            Estimated size in bytes
        """
        try:
            # For more accurate size estimation, we need to consider nested structures
            # sys.getsizeof only counts the container, not the contents

            total_size = 0

            # Estimate messages size by serializing to JSON
            # This gives us a better approximation of actual data size
            import json

            messages_json = json.dumps(messages)
            total_size += len(messages_json.encode("utf-8"))

            # Add stats size
            stats_json = json.dumps(stats)
            total_size += len(stats_json.encode("utf-8"))

            # Add Python object overhead (roughly 50% for dictionaries and lists)
            total_size = int(total_size * 1.5)

            return total_size
        except Exception as e:
            logger.error(f"Error estimating size: {e}")
            # Fallback: rough estimate based on message count
            return len(messages) * 1000  # ~1KB per message
