"""
Unit Tests for API Quota Management Service

Comprehensive test suite for API quota management including:
- Rate limiting and quota enforcement
- Usage analytics and aggregation
- API key rotation and management
- Multi-tenant quota isolation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.services.api_quota_management import APIQuotaManagementService

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit
from app.core.exceptions import NotFoundError, ValidationError, QuotaExceededError


class TestAPIQuotaManagementService:
    """Test suite for API Quota Management Service."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def quota_service(self, mock_db):
        """API quota management service instance with mocked database."""
        with patch('app.services.api_quota_management.WebhookTriggers') as mock_webhook_class:
            mock_webhook_class.return_value = Mock()
            return APIQuotaManagementService(mock_db)
    
    @pytest.fixture
    def sample_api_key_config(self):
        """Sample API key configuration for testing."""
        return {
            'key': 'test_api_key_123',
            'reseller_id': 1,
            'is_active': True,
            'daily_quota': 10000,
            'monthly_quota': 300000,
            'rate_limits': [
                {'requests': 100, 'window_seconds': 60},
                {'requests': 1000, 'window_seconds': 3600}
            ]
        }
    
    def test_check_rate_limit_allowed(self, quota_service, sample_api_key_config):
        """Test rate limit check when within limits."""
        with patch.object(quota_service, '_get_api_key_config', return_value=sample_api_key_config):
            with patch.object(quota_service, '_check_individual_rate_limit', return_value=True):
                with patch.object(quota_service, '_record_api_call'):
                    result = quota_service.check_rate_limit('test_api_key_123', '/customers')
                    
                    assert result['allowed'] is True
                    assert 'remaining_calls' in result
                    assert 'reset_time' in result
    
    def test_check_rate_limit_exceeded(self, quota_service, sample_api_key_config):
        """Test rate limit check when limit is exceeded."""
        with patch.object(quota_service, '_get_api_key_config', return_value=sample_api_key_config):
            with patch.object(quota_service, '_check_individual_rate_limit', return_value=False):
                result = quota_service.check_rate_limit('test_api_key_123', '/customers')
                
                assert result['allowed'] is False
                assert result['reason'] == 'rate_limit_exceeded'
                assert 'retry_after_seconds' in result
    
    def test_check_rate_limit_invalid_key(self, quota_service):
        """Test rate limit check with invalid API key."""
        with patch.object(quota_service, '_get_api_key_config', return_value=None):
            with pytest.raises(NotFoundError):
                quota_service.check_rate_limit('invalid_key', '/customers')
    
    def test_check_rate_limit_inactive_key(self, quota_service):
        """Test rate limit check with inactive API key."""
        inactive_config = {
            'key': 'inactive_key',
            'is_active': False
        }
        
        with patch.object(quota_service, '_get_api_key_config', return_value=inactive_config):
            with pytest.raises(ValidationError):
                quota_service.check_rate_limit('inactive_key', '/customers')
    
    def test_check_quota_limits_within_quota(self, quota_service, sample_api_key_config):
        """Test quota check when within limits."""
        with patch.object(quota_service, '_get_api_key_config', return_value=sample_api_key_config):
            with patch.object(quota_service, '_get_daily_usage', return_value=5000):
                with patch.object(quota_service, '_get_monthly_usage', return_value=150000):
                    result = quota_service.check_quota_limits('test_api_key_123')
                    
                    assert result['within_quota'] is True
                    assert result['daily_usage'] == 5000
                    assert result['monthly_usage'] == 150000
    
    def test_check_quota_limits_daily_exceeded(self, quota_service, sample_api_key_config):
        """Test quota check when daily limit is exceeded."""
        with patch.object(quota_service, '_get_api_key_config', return_value=sample_api_key_config):
            with patch.object(quota_service, '_get_daily_usage', return_value=12000):  # Over 10000 limit
                with patch.object(quota_service, '_get_monthly_usage', return_value=150000):
                    result = quota_service.check_quota_limits('test_api_key_123')
                    
                    assert result['within_quota'] is False
                    assert result['quota_type'] == 'daily'
                    assert result['usage'] == 12000
                    assert result['limit'] == 10000
    
    def test_check_quota_limits_monthly_exceeded(self, quota_service, sample_api_key_config):
        """Test quota check when monthly limit is exceeded."""
        with patch.object(quota_service, '_get_api_key_config', return_value=sample_api_key_config):
            with patch.object(quota_service, '_get_daily_usage', return_value=5000):
                with patch.object(quota_service, '_get_monthly_usage', return_value=350000):  # Over 300000 limit
                    result = quota_service.check_quota_limits('test_api_key_123')
                    
                    assert result['within_quota'] is False
                    assert result['quota_type'] == 'monthly'
                    assert result['usage'] == 350000
                    assert result['limit'] == 300000
    
    def test_individual_rate_limit_check_within_limit(self, quota_service):
        """Test individual rate limit check when within limit."""
        # Clear cache first
        quota_service._rate_limit_cache.clear()
        
        rule = {'requests': 10, 'window_seconds': 60}
        
        # Add some calls but stay within limit
        now = datetime.now(timezone.utc)
        cache_key = "test_key:/test:60"
        quota_service._rate_limit_cache[cache_key]['calls'] = [
            now - timedelta(seconds=30),
            now - timedelta(seconds=20),
            now - timedelta(seconds=10)
        ]
        
        result = quota_service._check_individual_rate_limit('test_key', '/test', rule)
        assert result is True
    
    def test_individual_rate_limit_check_exceeded(self, quota_service):
        """Test individual rate limit check when limit is exceeded."""
        # Clear cache first
        quota_service._rate_limit_cache.clear()
        
        rule = {'requests': 3, 'window_seconds': 60}
        
        # Add calls that exceed the limit
        now = datetime.now(timezone.utc)
        cache_key = "test_key:/test:60"
        quota_service._rate_limit_cache[cache_key]['calls'] = [
            now - timedelta(seconds=30),
            now - timedelta(seconds=20),
            now - timedelta(seconds=10)
        ]
        
        result = quota_service._check_individual_rate_limit('test_key', '/test', rule)
        assert result is False
    
    def test_record_api_call(self, quota_service, sample_api_key_config):
        """Test API call recording."""
        with patch.object(quota_service, '_get_api_key_config', return_value=sample_api_key_config):
            quota_service._record_api_call('test_key', '/customers')
            
            # Check that calls were recorded in cache
            cache_60 = quota_service._rate_limit_cache['test_key:/customers:60']['calls']
            cache_3600 = quota_service._rate_limit_cache['test_key:/customers:3600']['calls']
            
            assert len(cache_60) == 1
            assert len(cache_3600) == 1
    
    def test_aggregate_daily_usage_no_calls(self, quota_service):
        """Test daily usage aggregation with no API calls."""
        test_date = datetime.now(timezone.utc).date()
        
        with patch.object(quota_service, '_get_api_calls_for_date', return_value=[]):
            result = quota_service.aggregate_daily_usage(test_date)
            
            assert result['api_keys_processed'] == 0
            assert result['total_calls'] == 0
            assert result['date'] == test_date.isoformat()
    
    def test_aggregate_daily_usage_with_calls(self, quota_service):
        """Test daily usage aggregation with API calls."""
        test_date = datetime.now(timezone.utc).date()
        mock_calls = [
            {
                'api_key': 'key1',
                'endpoint': '/customers',
                'status_code': 200,
                'reseller_id': 1
            },
            {
                'api_key': 'key1',
                'endpoint': '/services',
                'status_code': 404,
                'reseller_id': 1
            },
            {
                'api_key': 'key2',
                'endpoint': '/customers',
                'status_code': 200,
                'reseller_id': 2
            }
        ]
        
        with patch.object(quota_service, '_get_api_calls_for_date', return_value=mock_calls):
            with patch.object(quota_service, '_store_daily_aggregation') as mock_store:
                mock_store.return_value = {'api_key': 'test', 'total_calls': 1}
                
                result = quota_service.aggregate_daily_usage(test_date)
                
                assert result['api_keys_processed'] == 2  # key1 and key2
                assert result['total_calls'] == 3
                assert mock_store.call_count == 2
    
    def test_get_usage_analytics(self, quota_service, sample_api_key_config):
        """Test usage analytics retrieval."""
        with patch.object(quota_service, '_get_api_key_config', return_value=sample_api_key_config):
            with patch.object(quota_service, '_get_usage_data', return_value=[]):
                with patch.object(quota_service, '_calculate_usage_analytics') as mock_calc:
                    mock_analytics = {
                        'total_calls': 45000,
                        'average_calls_per_day': 1500,
                        'success_rate': 98.5
                    }
                    mock_calc.return_value = mock_analytics
                    
                    result = quota_service.get_usage_analytics('test_key', 30)
                    
                    assert result['api_key'] == 'test_key'
                    assert result['reseller_id'] == sample_api_key_config['reseller_id']
                    assert result['period_days'] == 30
                    assert result['analytics'] == mock_analytics
    
    def test_get_usage_analytics_invalid_key(self, quota_service):
        """Test usage analytics with invalid API key."""
        with patch.object(quota_service, '_get_api_key_config', return_value=None):
            with pytest.raises(NotFoundError):
                quota_service.get_usage_analytics('invalid_key', 30)
    
    def test_rotate_api_key_success(self, quota_service, sample_api_key_config):
        """Test successful API key rotation."""
        new_key = 'new_api_key_456'
        
        with patch.object(quota_service, '_get_api_key_config', return_value=sample_api_key_config):
            with patch.object(quota_service, '_generate_new_api_key', return_value=new_key):
                with patch.object(quota_service, '_store_api_key_config'):
                    with patch.object(quota_service, '_deactivate_api_key'):
                        with patch.object(quota_service.webhook_triggers, 'api_key_rotated') as mock_webhook:
                            result = quota_service.rotate_api_key('old_key')
                            
                            assert result['new_api_key'] == new_key
                            assert 'old_api_key_expires_at' in result
                            assert 'rotation_time' in result
                            
                            mock_webhook.assert_called_once()
    
    def test_rotate_api_key_not_found(self, quota_service):
        """Test API key rotation with non-existent key."""
        with patch.object(quota_service, '_get_api_key_config', return_value=None):
            with pytest.raises(NotFoundError):
                quota_service.rotate_api_key('nonexistent_key')
    
    def test_get_remaining_calls(self, quota_service):
        """Test getting remaining calls for rate limits."""
        rate_limits = [
            {'requests': 100, 'window_seconds': 60},
            {'requests': 1000, 'window_seconds': 3600}
        ]
        
        # Set up cache with some calls
        cache_60 = quota_service._rate_limit_cache['test_key:/test:60']['calls']
        cache_3600 = quota_service._rate_limit_cache['test_key:/test:3600']['calls']
        
        now = datetime.now(timezone.utc)
        cache_60.extend([now - timedelta(seconds=30)] * 25)  # 25 calls in last minute
        cache_3600.extend([now - timedelta(seconds=1800)] * 200)  # 200 calls in last hour
        
        result = quota_service._get_remaining_calls('test_key', '/test', rate_limits)
        
        assert result['60s'] == 75  # 100 - 25
        assert result['3600s'] == 800  # 1000 - 200
    
    def test_get_daily_reset_time(self, quota_service):
        """Test getting daily quota reset time."""
        reset_time_str = quota_service._get_daily_reset_time()
        reset_time = datetime.fromisoformat(reset_time_str.replace('Z', '+00:00'))
        
        # Should be tomorrow at midnight UTC
        now = datetime.now(timezone.utc)
        expected_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        assert reset_time.date() == expected_reset.date()
        assert reset_time.hour == 0
        assert reset_time.minute == 0
    
    def test_get_monthly_reset_time(self, quota_service):
        """Test getting monthly quota reset time."""
        reset_time_str = quota_service._get_monthly_reset_time()
        reset_time = datetime.fromisoformat(reset_time_str.replace('Z', '+00:00'))
        
        # Should be first day of next month
        now = datetime.now(timezone.utc)
        if now.month == 12:
            expected_month = 1
            expected_year = now.year + 1
        else:
            expected_month = now.month + 1
            expected_year = now.year
        
        assert reset_time.month == expected_month
        assert reset_time.year == expected_year
        assert reset_time.day == 1
        assert reset_time.hour == 0
    
    def test_generate_new_api_key(self, quota_service):
        """Test new API key generation."""
        new_key = quota_service._generate_new_api_key()
        
        assert new_key.startswith('isp_')
        assert len(new_key) > 10  # Should be reasonably long
        
        # Generate another key and ensure they're different
        another_key = quota_service._generate_new_api_key()
        assert new_key != another_key
    
    def test_calculate_usage_analytics(self, quota_service):
        """Test usage analytics calculation."""
        mock_usage_data = [
            {'endpoint': '/customers', 'calls': 1000, 'success': 980},
            {'endpoint': '/services', 'calls': 800, 'success': 790},
            {'endpoint': '/billing', 'calls': 500, 'success': 495}
        ]
        
        result = quota_service._calculate_usage_analytics(mock_usage_data, 30)
        
        # Check that all expected analytics are present
        assert 'total_calls' in result
        assert 'average_calls_per_day' in result
        assert 'success_rate' in result
        assert 'most_used_endpoints' in result
        assert 'error_rate_by_endpoint' in result
    
    def test_cache_cleanup_on_rate_limit_check(self, quota_service):
        """Test that old entries are cleaned from rate limit cache."""
        rule = {'requests': 10, 'window_seconds': 60}
        cache_key = 'test_key:/test:60'
        
        now = datetime.now(timezone.utc)
        old_time = now - timedelta(seconds=120)  # 2 minutes ago (outside window)
        recent_time = now - timedelta(seconds=30)  # 30 seconds ago (within window)
        
        # Add both old and recent calls
        quota_service._rate_limit_cache[cache_key]['calls'] = [old_time, recent_time]
        
        # Check rate limit (this should clean old entries)
        quota_service._check_individual_rate_limit('test_key', '/test', rule)
        
        # Only recent call should remain
        remaining_calls = quota_service._rate_limit_cache[cache_key]['calls']
        assert len(remaining_calls) == 1
        assert remaining_calls[0] == recent_time
    
    @patch('app.services.api_quota_management.logger')
    def test_error_handling_in_check_rate_limit(self, mock_logger, quota_service):
        """Test error handling in rate limit checking."""
        with patch.object(quota_service, '_get_api_key_config', 
                         side_effect=Exception("Database error")):
            with pytest.raises(Exception):
                quota_service.check_rate_limit('test_key', '/test')
            
            mock_logger.error.assert_called()
    
    @patch('app.services.api_quota_management.logger')
    def test_error_handling_in_aggregate_daily_usage(self, mock_logger, quota_service):
        """Test error handling in daily usage aggregation."""
        with patch.object(quota_service, '_get_api_calls_for_date', 
                         side_effect=Exception("Database error")):
            with pytest.raises(Exception):
                quota_service.aggregate_daily_usage()
            
            mock_logger.error.assert_called()
    
    def test_webhook_integration_on_rotation(self, quota_service, sample_api_key_config):
        """Test webhook integration for API key rotation."""
        new_key = 'new_key_123'
        
        with patch.object(quota_service, '_get_api_key_config', return_value=sample_api_key_config):
            with patch.object(quota_service, '_generate_new_api_key', return_value=new_key):
                with patch.object(quota_service, '_store_api_key_config'):
                    with patch.object(quota_service, '_deactivate_api_key'):
                        with patch.object(quota_service.webhook_triggers, 'api_key_rotated') as mock_webhook:
                            quota_service.rotate_api_key('old_key')
                            
                            # Verify webhook was called with correct data
                            mock_webhook.assert_called_once()
                            call_args = mock_webhook.call_args[0][0]
                            
                            assert 'old_api_key' in call_args
                            assert 'new_api_key' in call_args
                            assert call_args['reseller_id'] == sample_api_key_config['reseller_id']
                            assert call_args['grace_period_hours'] == 24


# Integration tests would go here
class TestAPIQuotaManagementServiceIntegration:
    """Integration tests for API Quota Management Service."""
    
    @pytest.mark.skip(reason="Requires database models implementation")
    def test_real_quota_enforcement(self):
        """Test quota enforcement with real database."""
        pass
    
    @pytest.mark.skip(reason="Requires Redis for rate limiting")
    def test_redis_rate_limiting(self):
        """Test rate limiting with Redis backend."""
        pass
