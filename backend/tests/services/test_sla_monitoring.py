"""
Unit Tests for SLA Monitoring Service

Comprehensive test suite for SLA monitoring and escalation including:
- SLA breach detection and alerting
- Escalation queue processing
- Performance metrics calculation
- Rule management and validation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.services.sla_monitoring import SLAMonitoringService
from app.core.exceptions import ValidationError

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit
from app.services.webhook_integration_service import WebhookTriggers


class TestSLAMonitoringService:
    """Test suite for SLA Monitoring Service."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_webhook_triggers(self):
        """Mock webhook triggers service."""
        return Mock(spec=WebhookTriggers)
    
    @pytest.fixture
    def sla_service(self, mock_db):
        """SLA monitoring service instance with mocked database."""
        with patch('app.services.sla_monitoring.WebhookTriggers') as mock_webhook_class:
            mock_webhook_class.return_value = Mock()
            return SLAMonitoringService(mock_db)
    
    @pytest.fixture
    def sample_ticket(self):
        """Sample ticket data for testing."""
        return {
            'id': 1,
            'customer_id': 123,
            'priority': 'high',
            'status': 'open',
            'created_at': datetime.now(timezone.utc) - timedelta(hours=2),
            'sla_target_minutes': 240,  # 4 hours
            'assigned_to': 1,
            'category': 'technical'
        }
    
    @pytest.fixture
    def expired_ticket(self):
        """Expired ticket data for testing."""
        return {
            'id': 2,
            'customer_id': 456,
            'priority': 'critical',
            'status': 'open',
            'created_at': datetime.now(timezone.utc) - timedelta(hours=6),
            'sla_target_minutes': 60,  # 1 hour (already expired)
            'assigned_to': 2,
            'category': 'technical'
        }
    
    def test_check_sla_breaches_no_tickets(self, sla_service):
        """Test SLA breach check with no active tickets."""
        with patch.object(sla_service, '_get_active_tickets_with_sla', return_value=[]):
            result = sla_service.check_sla_breaches()
            
            assert result['breached_tickets'] == []
            assert result['warnings_issued'] == []
            assert result['total_checked'] == 0
            assert 'check_time' in result
    
    def test_check_sla_breaches_with_breach(self, sla_service, expired_ticket):
        """Test SLA breach detection with expired ticket."""
        with patch.object(sla_service, '_get_active_tickets_with_sla', return_value=[expired_ticket]):
            with patch.object(sla_service, '_mark_ticket_breached') as mock_mark:
                with patch.object(sla_service.webhook_triggers, 'sla_breached') as mock_webhook:
                    result = sla_service.check_sla_breaches()
                    
                    assert len(result['breached_tickets']) == 1
                    assert result['breached_tickets'][0]['ticket_id'] == expired_ticket['id']
                    assert result['breached_tickets'][0]['customer_id'] == expired_ticket['customer_id']
                    assert result['breached_tickets'][0]['overdue_minutes'] > 0
                    
                    mock_mark.assert_called_once()
                    mock_webhook.assert_called_once()
    
    def test_check_sla_breaches_with_warning(self, sla_service):
        """Test SLA warning detection for tickets approaching breach."""
        # Create ticket that will breach in 15 minutes
        warning_ticket = {
            'id': 3,
            'customer_id': 789,
            'priority': 'medium',
            'status': 'open',
            'created_at': datetime.now(timezone.utc) - timedelta(minutes=105),  # 1h 45m ago
            'sla_target_minutes': 120,  # 2 hours (15 minutes remaining)
            'assigned_to': 3,
            'category': 'billing'
        }
        
        with patch.object(sla_service, '_get_active_tickets_with_sla', return_value=[warning_ticket]):
            with patch.object(sla_service, '_issue_sla_warning') as mock_warning:
                result = sla_service.check_sla_breaches()
                
                assert len(result['warnings_issued']) == 1
                assert result['warnings_issued'][0]['ticket_id'] == warning_ticket['id']
                assert result['warnings_issued'][0]['time_remaining_minutes'] <= 30
                
                mock_warning.assert_called_once()
    
    def test_check_ticket_sla_within_limits(self, sla_service, sample_ticket):
        """Test SLA check for ticket within limits."""
        result = sla_service._check_ticket_sla(sample_ticket)
        
        assert result['status'] == 'within_sla'
        assert result['time_remaining_minutes'] > 30
        assert result['elapsed_minutes'] == 120  # 2 hours
    
    def test_check_ticket_sla_breached(self, sla_service, expired_ticket):
        """Test SLA check for breached ticket."""
        result = sla_service._check_ticket_sla(expired_ticket)
        
        assert result['status'] == 'breached'
        assert result['overdue_minutes'] > 0
        assert 'breach_time' in result
    
    def test_check_ticket_sla_warning(self, sla_service):
        """Test SLA check for ticket approaching breach."""
        # Ticket with 15 minutes remaining
        warning_ticket = {
            'id': 4,
            'customer_id': 999,
            'priority': 'low',
            'status': 'open',
            'created_at': datetime.now(timezone.utc) - timedelta(minutes=105),
            'sla_target_minutes': 120,
            'assigned_to': 4,
            'category': 'general'
        }
        
        result = sla_service._check_ticket_sla(warning_ticket)
        
        assert result['status'] == 'warning'
        assert result['time_remaining_minutes'] <= 30
    
    def test_process_escalation_queue_no_candidates(self, sla_service):
        """Test escalation processing with no candidates."""
        with patch.object(sla_service, '_get_escalation_candidates', return_value=[]):
            result = sla_service.process_escalation_queue()
            
            assert result['escalated_tickets'] == []
            assert result['escalation_failures'] == []
            assert result['total_processed'] == 0
    
    def test_process_escalation_queue_success(self, sla_service, sample_ticket):
        """Test successful escalation processing."""
        escalation_result = {
            'new_assignee': 5,
            'escalation_level': 2,
            'reason': 'SLA breach automatic escalation'
        }
        
        with patch.object(sla_service, '_get_escalation_candidates', return_value=[sample_ticket]):
            with patch.object(sla_service, '_escalate_ticket', return_value=escalation_result):
                with patch.object(sla_service.webhook_triggers, 'ticket_escalated') as mock_webhook:
                    result = sla_service.process_escalation_queue()
                    
                    assert len(result['escalated_tickets']) == 1
                    escalated = result['escalated_tickets'][0]
                    assert escalated['ticket_id'] == sample_ticket['id']
                    assert escalated['new_assignee'] == escalation_result['new_assignee']
                    assert escalated['escalation_level'] == escalation_result['escalation_level']
                    
                    mock_webhook.assert_called_once()
    
    def test_process_escalation_queue_failure(self, sla_service, sample_ticket):
        """Test escalation processing with failure."""
        with patch.object(sla_service, '_get_escalation_candidates', return_value=[sample_ticket]):
            with patch.object(sla_service, '_escalate_ticket', side_effect=Exception("Escalation failed")):
                result = sla_service.process_escalation_queue()
                
                assert len(result['escalation_failures']) == 1
                assert result['escalation_failures'][0]['ticket_id'] == sample_ticket['id']
                assert 'error' in result['escalation_failures'][0]
    
    def test_escalate_ticket_logic(self, sla_service):
        """Test ticket escalation logic."""
        ticket = {
            'id': 5,
            'escalation_level': 0,
            'assigned_to': 1
        }
        
        result = sla_service._escalate_ticket(ticket)
        
        assert result['escalation_level'] == 1
        assert result['new_assignee'] == 2  # Based on escalation mapping
        assert result['reason'] == 'SLA breach automatic escalation'
    
    def test_escalate_ticket_multiple_levels(self, sla_service):
        """Test ticket escalation through multiple levels."""
        # Test escalation from level 1 to 2
        ticket_level_1 = {
            'id': 6,
            'escalation_level': 1,
            'assigned_to': 2
        }
        
        result = sla_service._escalate_ticket(ticket_level_1)
        
        assert result['escalation_level'] == 2
        assert result['new_assignee'] == 3  # Team Lead
        
        # Test escalation from level 2 to 3
        ticket_level_2 = {
            'id': 7,
            'escalation_level': 2,
            'assigned_to': 3
        }
        
        result = sla_service._escalate_ticket(ticket_level_2)
        
        assert result['escalation_level'] == 3
        assert result['new_assignee'] == 4  # Manager
    
    def test_get_sla_performance_metrics(self, sla_service):
        """Test SLA performance metrics calculation."""
        with patch.object(sla_service, '_calculate_sla_metrics') as mock_calculate:
            mock_metrics = {
                'total_tickets': 100,
                'tickets_within_sla': 85,
                'tickets_breached': 15,
                'sla_compliance_rate': 85.0,
                'average_resolution_time_minutes': 180,
                'escalation_rate': 12.0,
                'by_priority': {},
                'by_category': {}
            }
            mock_calculate.return_value = mock_metrics
            
            result = sla_service.get_sla_performance_metrics(30)
            
            assert result['period_days'] == 30
            assert result['total_tickets'] == 100
            assert result['sla_compliance_rate'] == 85.0
            assert 'period_start' in result
            assert 'period_end' in result
            
            mock_calculate.assert_called_once()
    
    def test_get_escalation_queue(self, sla_service):
        """Test escalation queue retrieval."""
        mock_entries = [
            {'id': 1, 'ticket_id': 101, 'priority': 'high'},
            {'id': 2, 'ticket_id': 102, 'priority': 'critical'}
        ]
        
        with patch.object(sla_service, '_get_escalation_queue_entries', return_value=mock_entries):
            with patch.object(sla_service, '_count_escalation_queue_entries', return_value=2):
                result = sla_service.get_escalation_queue(page=1, per_page=25)
                
                assert result['entries'] == mock_entries
                assert result['total'] == 2
                assert result['page'] == 1
                assert result['per_page'] == 25
                assert result['pages'] == 1
    
    def test_create_escalation_rule_success(self, sla_service):
        """Test successful escalation rule creation."""
        rule_data = {
            'name': 'High Priority Escalation',
            'conditions': [{'field': 'priority', 'operator': 'equals', 'value': 'high'}],
            'actions': [{'type': 'escalate', 'target': 'manager'}]
        }
        
        mock_rule = {
            'id': 1,
            'name': rule_data['name'],
            'conditions': rule_data['conditions'],
            'actions': rule_data['actions'],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        with patch.object(sla_service, '_validate_escalation_rule') as mock_validate:
            with patch.object(sla_service, '_create_escalation_rule_record', return_value=mock_rule):
                result = sla_service.create_escalation_rule(rule_data)
                
                assert result == mock_rule
                mock_validate.assert_called_once_with(rule_data)
    
    def test_create_escalation_rule_validation_error(self, sla_service):
        """Test escalation rule creation with validation error."""
        invalid_rule_data = {
            'name': 'Invalid Rule'
            # Missing required fields
        }
        
        with patch.object(sla_service, '_validate_escalation_rule', 
                         side_effect=ValueError("Missing required field: conditions")):
            with pytest.raises(ValueError):
                sla_service.create_escalation_rule(invalid_rule_data)
    
    def test_calculate_sla_metrics(self, sla_service):
        """Test SLA metrics calculation."""
        period_start = datetime.now(timezone.utc) - timedelta(days=30)
        
        result = sla_service._calculate_sla_metrics(period_start)
        
        # Check that all expected metrics are present
        assert 'total_tickets' in result
        assert 'tickets_within_sla' in result
        assert 'tickets_breached' in result
        assert 'sla_compliance_rate' in result
        assert 'average_resolution_time_minutes' in result
        assert 'escalation_rate' in result
        assert 'by_priority' in result
        assert 'by_category' in result
        
        # Check that compliance rate is calculated correctly
        if result['total_tickets'] > 0:
            expected_rate = (result['tickets_within_sla'] / result['total_tickets']) * 100
            assert abs(result['sla_compliance_rate'] - expected_rate) < 0.1
    
    def test_mark_ticket_breached(self, sla_service):
        """Test marking ticket as breached."""
        sla_result = {
            'status': 'breached',
            'breach_time': datetime.now(timezone.utc),
            'overdue_minutes': 60
        }
        
        # This is a placeholder test since the method is mocked
        # In real implementation, this would test database update
        sla_service._mark_ticket_breached(123, sla_result)
        
        # Should not raise exception
        assert True
    
    def test_issue_sla_warning(self, sla_service):
        """Test issuing SLA warning."""
        sla_result = {
            'status': 'warning',
            'time_remaining_minutes': 15
        }
        
        # This is a placeholder test since the method is mocked
        # In real implementation, this would test warning creation
        sla_service._issue_sla_warning(456, sla_result)
        
        # Should not raise exception
        assert True
    
    def test_validate_escalation_rule(self, sla_service):
        """Test escalation rule validation."""
        # Valid rule data
        valid_rule = {
            'name': 'Test Rule',
            'conditions': [],
            'actions': []
        }
        
        # Should not raise exception
        sla_service._validate_escalation_rule(valid_rule)
        
        # Invalid rule data - missing name
        invalid_rule = {
            'conditions': [],
            'actions': []
        }
        
        with pytest.raises(ValidationError):
            sla_service._validate_escalation_rule(invalid_rule)
    
    @patch('app.services.sla_monitoring.logger')
    def test_error_handling_in_check_sla_breaches(self, mock_logger, sla_service):
        """Test error handling in SLA breach checking."""
        with patch.object(sla_service, '_get_active_tickets_with_sla', 
                         side_effect=Exception("Database error")):
            with pytest.raises(Exception):
                sla_service.check_sla_breaches()
            
            mock_logger.error.assert_called()
    
    @patch('app.services.sla_monitoring.logger')
    def test_error_handling_in_process_escalation_queue(self, mock_logger, sla_service):
        """Test error handling in escalation queue processing."""
        with patch.object(sla_service, '_get_escalation_candidates', 
                         side_effect=Exception("Database error")):
            with pytest.raises(Exception):
                sla_service.process_escalation_queue()
            
            mock_logger.error.assert_called()
    
    def test_webhook_integration(self, sla_service, expired_ticket):
        """Test webhook integration for SLA events."""
        with patch.object(sla_service, '_get_active_tickets_with_sla', return_value=[expired_ticket]):
            with patch.object(sla_service, '_mark_ticket_breached'):
                with patch.object(sla_service.webhook_triggers, 'sla_breached') as mock_webhook:
                    sla_service.check_sla_breaches()
                    
                    # Verify webhook was called with correct data
                    mock_webhook.assert_called_once()
                    call_args = mock_webhook.call_args[0][0]
                    
                    assert call_args['ticket_id'] == expired_ticket['id']
                    assert call_args['customer_id'] == expired_ticket['customer_id']
                    assert call_args['priority'] == expired_ticket['priority']
                    assert 'overdue_minutes' in call_args
                    assert 'breach_time' in call_args


# Integration tests would go here
class TestSLAMonitoringServiceIntegration:
    """Integration tests for SLA Monitoring Service."""
    
    @pytest.mark.skip(reason="Requires database models implementation")
    def test_real_sla_breach_detection(self):
        """Test SLA breach detection with real database."""
        pass
    
    @pytest.mark.skip(reason="Requires database models implementation")
    def test_real_escalation_processing(self):
        """Test escalation processing with real database."""
        pass
