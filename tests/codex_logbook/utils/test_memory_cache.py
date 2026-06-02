"""
Tests for the memory cache module.
"""


import pytest

from codex_logbook.utils.memory_cache import MemoryCache


class TestMemoryCache:
    """Test cases for MemoryCache class."""
    
    def test_basic_get_put(self):
        """Test basic cache operations."""
        cache = MemoryCache(max_projects=3)
        
        # Test miss
        result = cache.get("/path/to/project1")
        assert result is None
        assert cache.misses == 1
        assert cache.hits == 0
        
        # Test put and hit
        messages = [{"id": 1, "content": "test"}]
        stats = {"total": 1}
        
        assert cache.put("/path/to/project1", messages, stats)
        
        result = cache.get("/path/to/project1")
        assert result is not None
        assert result[0] == messages
        assert result[1] == stats
        assert cache.hits == 1
        assert cache.misses == 1
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = MemoryCache(max_projects=2)
        
        # Fill cache
        cache.put("/project1", [{"id": 1}], {"total": 1})
        cache.put("/project2", [{"id": 2}], {"total": 2})
        
        assert len(cache.cache) == 2
        
        # Add third project - should evict project1
        # Use force=True to bypass protection window
        cache.put("/project3", [{"id": 3}], {"total": 3}, force=True)
        
        assert len(cache.cache) == 2
        assert cache.get("/project1") is None  # Evicted
        assert cache.get("/project2") is not None
        assert cache.get("/project3") is not None
        assert cache.evictions == 1
    
    def test_lru_ordering(self):
        """Test that LRU order is maintained on access."""
        cache = MemoryCache(max_projects=3)
        
        # Add three projects
        cache.put("/project1", [{"id": 1}], {"total": 1})
        cache.put("/project2", [{"id": 2}], {"total": 2})
        cache.put("/project3", [{"id": 3}], {"total": 3})
        
        # Access project1 - moves to end
        cache.get("/project1")
        
        # Add project4 - should evict project2 (least recently used)
        # Use force=True to bypass protection window
        cache.put("/project4", [{"id": 4}], {"total": 4}, force=True)
        
        assert cache.get("/project2") is None  # Evicted
        assert cache.get("/project1") is not None  # Still there
        assert cache.get("/project3") is not None  # Still there
        assert cache.get("/project4") is not None  # Still there
    
    def test_size_limit(self):
        """Test that projects exceeding size limit are rejected."""
        cache = MemoryCache(max_projects=5, max_mb_per_project=1)  # 1MB limit
        
        # Create large data (>1MB)
        large_messages = [{"id": i, "content": "x" * 1000} for i in range(2000)]
        stats = {"total": len(large_messages)}
        
        # Should reject due to size
        assert not cache.put("/large_project", large_messages, stats)
        assert cache.size_rejections == 1
        assert cache.get("/large_project") is None
    
    def test_invalidate(self):
        """Test cache invalidation."""
        cache = MemoryCache()
        
        cache.put("/project1", [{"id": 1}], {"total": 1})
        assert cache.get("/project1") is not None
        
        # Invalidate
        assert cache.invalidate("/project1")
        assert cache.get("/project1") is None
        
        # Invalidate non-existent
        assert not cache.invalidate("/project2")
    
    def test_clear(self):
        """Test clearing all cache."""
        cache = MemoryCache()
        
        cache.put("/project1", [{"id": 1}], {"total": 1})
        cache.put("/project2", [{"id": 2}], {"total": 2})
        
        assert len(cache.cache) == 2
        
        cache.clear()
        assert len(cache.cache) == 0
        assert cache.get("/project1") is None
        assert cache.get("/project2") is None
    
    def test_get_stats(self):
        """Test cache statistics."""
        cache = MemoryCache(max_projects=3)
        
        # Initial stats
        stats = cache.get_stats()
        assert stats['projects_cached'] == 0
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0.0
        
        # Add some data and access
        cache.put("/project1", [{"id": 1}], {"total": 1})
        cache.get("/project1")  # Hit
        cache.get("/project2")  # Miss
        
        stats = cache.get_stats()
        assert stats['projects_cached'] == 1
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 50.0
        assert '/project1' in stats['cache_keys']
    
    def test_get_project_info(self):
        """Test getting info about a cached project."""
        cache = MemoryCache()
        
        messages = [{"id": 1}, {"id": 2}]
        stats = {"total": 2}
        
        cache.put("/project1", messages, stats)
        
        # Get info for cached project
        info = cache.get_project_info("/project1")
        assert info is not None
        assert info['path'] == "/project1"
        assert info['message_count'] == 2
        assert 'size_mb' in info
        assert 'cached_at' in info
        assert 'age_seconds' in info
        
        # Get info for non-cached project
        info = cache.get_project_info("/project2")
        assert info is None
    
    def test_concurrent_access(self):
        """Test that cache handles concurrent access correctly."""
        cache = MemoryCache(max_projects=2)
        
        # Simulate concurrent puts
        cache.put("/project1", [{"id": 1}], {"total": 1})
        cache.put("/project2", [{"id": 2}], {"total": 2})
        
        # Access in different order
        assert cache.get("/project2") is not None
        assert cache.get("/project1") is not None
        
        # Cache should maintain consistency
        assert len(cache.cache) == 2
        assert cache.hits == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])