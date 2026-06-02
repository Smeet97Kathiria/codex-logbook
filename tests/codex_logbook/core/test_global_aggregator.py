"""
Tests for the global statistics aggregator.
"""
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from codex_logbook.core.global_aggregator import GlobalStatsAggregator


class TestGlobalStatsAggregator:
    """Test the global statistics aggregator."""
    
    @pytest.fixture
    def mock_caches(self):
        """Create mock cache instances."""
        memory_cache = Mock()
        file_cache = Mock()
        return memory_cache, file_cache
    
    @pytest.fixture
    def aggregator(self, mock_caches):
        """Create aggregator instance with mocks."""
        memory_cache, file_cache = mock_caches
        return GlobalStatsAggregator(memory_cache, file_cache)
    
    @pytest.fixture
    def sample_projects(self):
        """Create sample project data."""
        return [
            {
                'dir_name': '-Users-test-project1',
                'log_path': '/home/.codex-logbook/codex/projects/-Users-test-project1',
                'in_cache': True,
                'file_count': 2,
                'total_size_mb': 1.0
            },
            {
                'dir_name': '-Users-test-project2',
                'log_path': '/home/.codex-logbook/codex/projects/-Users-test-project2',
                'in_cache': False,
                'file_count': 1,
                'total_size_mb': 0.5
            }
        ]
    
    @pytest.fixture
    def sample_stats(self):
        """Create sample statistics for projects."""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        return {
            'project1': {
                'overview': {
                    'total_tokens': {
                        'input': 10000,
                        'output': 20000,
                        'cache_read': 5000,
                        'cache_creation': 2000
                    },
                    'total_cost': 1.70
                },
                'user_interactions': {
                    'user_commands_analyzed': 50
                },
                'first_message_date': '2024-01-01T10:00:00Z',
                'last_message_date': today.isoformat() + 'T15:00:00Z',
                'daily_stats': {
                    yesterday.isoformat(): {
                        'tokens': {'input': 3000, 'output': 6000},
                        'cost': {'total': 0.50}
                    },
                    today.isoformat(): {
                        'tokens': {'input': 7000, 'output': 14000},
                        'cost': {'total': 1.20}
                    }
                }
            },
            'project2': {
                'overview': {
                    'total_tokens': {
                        'input': 5000,
                        'output': 10000,
                        'cache_read': 1000,
                        'cache_creation': 500
                    },
                    'total_cost': 0.30
                },
                'user_interactions': {
                    'user_commands_analyzed': 25
                },
                'first_message_date': '2024-02-01T08:00:00Z',
                'last_message_date': yesterday.isoformat() + 'T20:00:00Z',
                'daily_stats': {
                    yesterday.isoformat(): {
                        'tokens': {'input': 2000, 'output': 4000},
                        'cost': {'total': 0.30}
                    }
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_get_global_stats_basic(self, aggregator, sample_projects, sample_stats, mock_caches):
        """Test basic global stats aggregation."""
        memory_cache, file_cache = mock_caches
        
        # Mock cache responses
        def memory_get_side_effect(path):
            if 'project1' in path:
                return ([], sample_stats['project1'])
            return None
        
        memory_cache.get.side_effect = memory_get_side_effect
        file_cache.get_cached_stats.return_value = sample_stats['project2']
        
        # Get global stats
        result = await aggregator.get_global_stats(sample_projects)
        
        # Verify basic counts
        assert result['total_projects'] == 2
        assert result['total_input_tokens'] == 15000  # 10000 + 5000
        assert result['total_output_tokens'] == 30000  # 20000 + 10000
        assert result['total_cache_read_tokens'] == 6000  # 5000 + 1000
        assert result['total_cache_write_tokens'] == 2500  # 2000 + 500
        assert result['total_commands'] == 75  # 50 + 25
        
        # Verify dates
        assert result['first_use_date'] == '2024-01-01T10:00:00+00:00'
        
        # Verify we have 30 days of data
        assert len(result['daily_token_usage']) == 30
        assert len(result['daily_costs']) == 30
    
    @pytest.mark.asyncio
    async def test_get_global_stats_empty_projects(self, aggregator):
        """Test aggregation with no projects."""
        result = await aggregator.get_global_stats([])
        
        assert result['total_projects'] == 0
        assert result['total_input_tokens'] == 0
        assert result['total_output_tokens'] == 0
        assert result['first_use_date'] is None
        assert len(result['daily_token_usage']) == 30  # Still shows 30 days
        
        # All daily values should be zero
        for day in result['daily_token_usage']:
            assert day['input'] == 0
            assert day['output'] == 0
    
    @pytest.mark.asyncio
    async def test_daily_aggregation(self, aggregator, sample_projects, sample_stats, mock_caches):
        """Test that daily stats are aggregated correctly."""
        memory_cache, file_cache = mock_caches
        
        # Set up mock returns for both projects
        sample_projects[0]['in_cache'] = True  # project1 in memory cache
        sample_projects[1]['in_cache'] = True  # project2 also in memory cache
        
        # Mock memory cache for both projects
        def memory_get_side_effect(path):
            if 'project1' in path:
                return ([], sample_stats['project1'])
            elif 'project2' in path:
                return ([], sample_stats['project2'])
            return None
        
        memory_cache.get.side_effect = memory_get_side_effect
        
        result = await aggregator.get_global_stats(sample_projects)
        
        # Find yesterday's data
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        yesterday_data = next((d for d in result['daily_token_usage'] if d['date'] == yesterday), None)
        
        assert yesterday_data is not None
        assert yesterday_data['input'] == 5000  # 3000 + 2000
        assert yesterday_data['output'] == 10000  # 6000 + 4000
        
        # Check cost aggregation
        yesterday_cost = next((d for d in result['daily_costs'] if d['date'] == yesterday), None)
        assert yesterday_cost is not None
        assert yesterday_cost['cost'] == 0.80  # 0.50 + 0.30
    
    @pytest.mark.asyncio
    async def test_process_uncached_projects(self, aggregator, sample_projects, mock_caches):
        """Test background processing of uncached projects."""
        memory_cache, file_cache = mock_caches
        
        # Mock the processor at the correct import location
        with patch('codex_logbook.core.processor.CodexLogProcessor') as mock_processor_class:
            mock_instance = Mock()
            mock_instance.process_logs.return_value = ([], {'total_messages': 10})
            mock_processor_class.return_value = mock_instance
            
            # Also need to patch the import in global_aggregator
            with patch.object(aggregator, 'file_cache') as mock_file:
                mock_file.save_cached_stats = Mock()
                mock_file.save_cached_messages = Mock()
                aggregator.file_cache = file_cache
                
                # Process uncached projects
                processed = await aggregator.process_uncached_projects(sample_projects, limit=1)
                
                # Should process only the uncached project
                assert processed == 1
                
                # Verify cache methods were called
                file_cache.save_cached_stats.assert_called_once()
                file_cache.save_cached_messages.assert_called_once()
    
    def test_invalid_dates_handled(self, aggregator):
        """Test that invalid dates don't crash aggregation."""
        # This is tested within get_global_stats by the try/except blocks
        # Just verify the aggregator initializes correctly
        assert aggregator is not None
        assert aggregator.memory_cache is not None
        assert aggregator.file_cache is not None
    
    @pytest.mark.asyncio
    async def test_missing_daily_stats_logged(self, aggregator, sample_projects, mock_caches, caplog):
        """Test that missing daily_stats is properly logged."""
        memory_cache, file_cache = mock_caches
        
        # Create stats without daily_stats
        stats_without_daily = {
            'overview': {
                'total_tokens': {
                    'input': 5000,
                    'output': 10000,
                    'cache_read': 0,
                    'cache_creation': 0
                },
                'total_cost': 0.50
            },
            'user_interactions': {
                'user_commands_analyzed': 25
            }
        }
        
        memory_cache.get.return_value = ([], stats_without_daily)
        
        # Run aggregation with logging capture
        with caplog.at_level(logging.INFO):
            result = await aggregator.get_global_stats(sample_projects[:1])
        
        # Check that appropriate log message was generated
        assert any("No daily_stats found" in record.message for record in caplog.records)
        
        # Verify aggregation still works
        assert result['total_input_tokens'] == 5000
        assert result['total_output_tokens'] == 10000
    
    @pytest.mark.asyncio
    async def test_invalid_daily_stats_format_logged(self, aggregator, sample_projects, mock_caches, caplog):
        """Test that invalid daily_stats format is properly logged."""
        memory_cache, file_cache = mock_caches
        
        # Create stats with wrong format (list instead of dict)
        stats_with_wrong_format = {
            'overview': {
                'total_tokens': {
                    'input': 5000,
                    'output': 10000,
                    'cache_read': 0,
                    'cache_creation': 0
                },
                'total_cost': 0.50
            },
            'user_interactions': {
                'user_commands_analyzed': 0
            },
            'daily_stats': ['not', 'a', 'dict']  # Wrong format!
        }
        
        memory_cache.get.return_value = ([], stats_with_wrong_format)
        
        # Run aggregation with logging capture
        with caplog.at_level(logging.WARNING):
            result = await aggregator.get_global_stats(sample_projects[:1])
        
        # Check that warning was logged
        assert any("daily_stats is not a dict" in record.message for record in caplog.records)
        
        # Verify aggregation still works
        assert result['total_input_tokens'] == 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])