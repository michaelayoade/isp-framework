"""
SLA Monitoring Service

Service layer for ticket SLA monitoring and escalation including:
- SLA breach detection and alerting
- Automatic escalation queue management
- SLA performance metrics and reporting
- Integration with communications for notifications
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.exceptions import ValidationError
from app.services.webhook_integration_service import WebhookTriggers
import logging

logger = logging.getLogger(__name__)


class SLAMonitoringService:
    """Service layer for SLA monitoring and escalation management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
    
    def check_sla_breaches(self) -> Dict[str, Any]:
        """Check for SLA breaches and mark tickets accordingly."""
        try:
            # Get all active tickets with SLA requirements
            active_tickets = self._get_active_tickets_with_sla()
            
            breached_tickets = []
            warnings_issued = []
            
            for ticket in active_tickets:
                sla_result = self._check_ticket_sla(ticket)
                
                if sla_result['status'] == 'breached':
                    # Mark ticket as breached
                    self._mark_ticket_breached(ticket['id'], sla_result)
                    breached_tickets.append({
                        'ticket_id': ticket['id'],
                        'customer_id': ticket['customer_id'],
                        'breach_time': sla_result['breach_time'],
                        'overdue_minutes': sla_result['overdue_minutes']
                    })
                    
                    # Trigger webhook for SLA breach
                    self.webhook_triggers.sla_breached({
                        'ticket_id': ticket['id'],
                        'customer_id': ticket['customer_id'],
                        'priority': ticket['priority'],
                        'sla_target_minutes': ticket['sla_target_minutes'],
                        'overdue_minutes': sla_result['overdue_minutes'],
                        'breach_time': sla_result['breach_time'].isoformat()
                    })
                    
                elif sla_result['status'] == 'warning':
                    # Issue warning for approaching breach
                    self._issue_sla_warning(ticket['id'], sla_result)
                    warnings_issued.append({
                        'ticket_id': ticket['id'],
                        'customer_id': ticket['customer_id'],
                        'time_remaining_minutes': sla_result['time_remaining_minutes']
                    })
            
            logger.info(f"SLA check completed: {len(breached_tickets)} breaches, {len(warnings_issued)} warnings")
            
            return {
                'breached_tickets': breached_tickets,
                'warnings_issued': warnings_issued,
                'total_checked': len(active_tickets),
                'check_time': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking SLA breaches: {e}")
            raise
    
    def process_escalation_queue(self) -> Dict[str, Any]:
        """Process tickets in the escalation queue."""
        try:
            # Get tickets eligible for escalation
            escalation_candidates = self._get_escalation_candidates()
            
            escalated_tickets = []
            escalation_failures = []
            
            for ticket in escalation_candidates:
                try:
                    escalation_result = self._escalate_ticket(ticket)
                    escalated_tickets.append({
                        'ticket_id': ticket['id'],
                        'customer_id': ticket['customer_id'],
                        'old_assignee': ticket.get('assigned_to'),
                        'new_assignee': escalation_result['new_assignee'],
                        'escalation_level': escalation_result['escalation_level']
                    })
                    
                    # Trigger webhook for escalation
                    self.webhook_triggers.ticket_escalated({
                        'ticket_id': ticket['id'],
                        'customer_id': ticket['customer_id'],
                        'old_assignee': ticket.get('assigned_to'),
                        'new_assignee': escalation_result['new_assignee'],
                        'escalation_level': escalation_result['escalation_level'],
                        'escalation_reason': escalation_result['reason'],
                        'escalated_at': datetime.now(timezone.utc).isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error escalating ticket {ticket['id']}: {e}")
                    escalation_failures.append({
                        'ticket_id': ticket['id'],
                        'error': str(e)
                    })
            
            logger.info(f"Escalation processing completed: {len(escalated_tickets)} escalated, {len(escalation_failures)} failures")
            
            return {
                'escalated_tickets': escalated_tickets,
                'escalation_failures': escalation_failures,
                'total_processed': len(escalation_candidates),
                'process_time': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing escalation queue: {e}")
            raise
    
    def get_sla_performance_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """Get SLA performance metrics for a given period."""
        try:
            period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get SLA statistics
            metrics = self._calculate_sla_metrics(period_start)
            
            return {
                'period_start': period_start.isoformat(),
                'period_end': datetime.now(timezone.utc).isoformat(),
                'period_days': period_days,
                'total_tickets': metrics['total_tickets'],
                'tickets_within_sla': metrics['tickets_within_sla'],
                'tickets_breached': metrics['tickets_breached'],
                'sla_compliance_rate': metrics['sla_compliance_rate'],
                'average_resolution_time_minutes': metrics['average_resolution_time_minutes'],
                'escalation_rate': metrics['escalation_rate'],
                'by_priority': metrics['by_priority'],
                'by_category': metrics['by_category']
            }
            
        except Exception as e:
            logger.error(f"Error calculating SLA metrics: {e}")
            raise
    
    def get_escalation_queue(self, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
        """Get current escalation queue with pagination."""
        try:
            # Get escalation queue entries
            escalation_entries = self._get_escalation_queue_entries(page, per_page)
            total_entries = self._count_escalation_queue_entries()
            
            return {
                'entries': escalation_entries,
                'total': total_entries,
                'page': page,
                'per_page': per_page,
                'pages': ((total_entries - 1) // per_page) + 1 if total_entries > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error retrieving escalation queue: {e}")
            raise
    
    def create_escalation_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new escalation rule."""
        try:
            # Validate rule data
            self._validate_escalation_rule(rule_data)
            
            # Create escalation rule
            rule = self._create_escalation_rule_record(rule_data)
            
            logger.info(f"Created escalation rule {rule['id']}")
            
            return rule
            
        except Exception as e:
            logger.error(f"Error creating escalation rule: {e}")
            raise
    
    def _get_active_tickets_with_sla(self) -> List[Dict[str, Any]]:
        """Get all active tickets that have SLA requirements."""
        # Placeholder - implement when ticket repository is available
        # This would query tickets with status in ['open', 'in_progress'] and sla_target_minutes is not null
        return [
            {
                'id': 1,
                'customer_id': 1,
                'priority': 'high',
                'status': 'open',
                'created_at': datetime.now(timezone.utc) - timedelta(hours=2),
                'sla_target_minutes': 240,  # 4 hours for high priority
                'assigned_to': 1,
                'category': 'technical'
            }
        ]
    
    def _check_ticket_sla(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Check SLA status for a specific ticket."""
        now = datetime.now(timezone.utc)
        created_at = ticket['created_at']
        sla_target_minutes = ticket['sla_target_minutes']
        
        # Calculate elapsed time
        elapsed_time = now - created_at
        elapsed_minutes = elapsed_time.total_seconds() / 60
        
        # Calculate SLA deadline
        sla_deadline = created_at + timedelta(minutes=sla_target_minutes)
        
        if now > sla_deadline:
            # SLA breached
            overdue_minutes = (now - sla_deadline).total_seconds() / 60
            return {
                'status': 'breached',
                'breach_time': sla_deadline,
                'overdue_minutes': int(overdue_minutes),
                'elapsed_minutes': int(elapsed_minutes)
            }
        elif (sla_deadline - now).total_seconds() / 60 <= 30:  # Warning 30 minutes before breach
            # SLA warning
            time_remaining_minutes = (sla_deadline - now).total_seconds() / 60
            return {
                'status': 'warning',
                'time_remaining_minutes': int(time_remaining_minutes),
                'elapsed_minutes': int(elapsed_minutes)
            }
        else:
            # SLA within limits
            time_remaining_minutes = (sla_deadline - now).total_seconds() / 60
            return {
                'status': 'within_sla',
                'time_remaining_minutes': int(time_remaining_minutes),
                'elapsed_minutes': int(elapsed_minutes)
            }
    
    def _mark_ticket_breached(self, ticket_id: int, sla_result: Dict[str, Any]):
        """Mark a ticket as SLA breached."""
        # Placeholder - implement when ticket repository is available
        # This would update the ticket with sla_breached=True, breach_time, etc.
        logger.info(f"Marked ticket {ticket_id} as SLA breached")
    
    def _issue_sla_warning(self, ticket_id: int, sla_result: Dict[str, Any]):
        """Issue SLA warning for a ticket approaching breach."""
        # Placeholder - implement when ticket repository is available
        # This would create a warning record and potentially send notifications
        logger.info(f"Issued SLA warning for ticket {ticket_id}")
    
    def _get_escalation_candidates(self) -> List[Dict[str, Any]]:
        """Get tickets that are candidates for escalation."""
        # Placeholder - implement when ticket repository is available
        # This would query tickets based on escalation rules (time, priority, breach status, etc.)
        return []
    
    def _escalate_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate a ticket to the next level."""
        # Placeholder - implement escalation logic
        # This would determine the next escalation level and assignee based on rules
        
        # Mock escalation logic
        current_level = ticket.get('escalation_level', 0)
        new_level = current_level + 1
        
        # Determine new assignee based on escalation level
        escalation_assignees = {
            1: 2,  # Level 1: Senior Support
            2: 3,  # Level 2: Team Lead
            3: 4,  # Level 3: Manager
            4: 5   # Level 4: Director
        }
        
        new_assignee = escalation_assignees.get(new_level, ticket.get('assigned_to'))
        
        # Update ticket
        # self.ticket_repo.update(ticket['id'], {
        #     'escalation_level': new_level,
        #     'assigned_to': new_assignee,
        #     'escalated_at': datetime.now(timezone.utc)
        # })
        
        return {
            'new_assignee': new_assignee,
            'escalation_level': new_level,
            'reason': 'SLA breach automatic escalation'
        }
    
    def _calculate_sla_metrics(self, period_start: datetime) -> Dict[str, Any]:
        """Calculate SLA performance metrics for a period."""
        # Placeholder - implement when ticket repository is available
        # This would aggregate ticket data to calculate performance metrics
        
        return {
            'total_tickets': 100,
            'tickets_within_sla': 85,
            'tickets_breached': 15,
            'sla_compliance_rate': 85.0,
            'average_resolution_time_minutes': 180,
            'escalation_rate': 12.0,
            'by_priority': {
                'critical': {'total': 10, 'within_sla': 8, 'compliance_rate': 80.0},
                'high': {'total': 25, 'within_sla': 20, 'compliance_rate': 80.0},
                'medium': {'total': 40, 'within_sla': 36, 'compliance_rate': 90.0},
                'low': {'total': 25, 'within_sla': 21, 'compliance_rate': 84.0}
            },
            'by_category': {
                'technical': {'total': 60, 'within_sla': 50, 'compliance_rate': 83.3},
                'billing': {'total': 25, 'within_sla': 22, 'compliance_rate': 88.0},
                'general': {'total': 15, 'within_sla': 13, 'compliance_rate': 86.7}
            }
        }
    
    def _get_escalation_queue_entries(self, page: int, per_page: int) -> List[Dict[str, Any]]:
        """Get escalation queue entries with pagination."""
        # Placeholder - implement when escalation queue repository is available
        return []
    
    def _count_escalation_queue_entries(self) -> int:
        """Count total escalation queue entries."""
        # Placeholder - implement when escalation queue repository is available
        return 0
    
    def _validate_escalation_rule(self, rule_data: Dict[str, Any]):
        """Validate escalation rule data."""
        required_fields = ['name', 'conditions', 'actions']
        for field in required_fields:
            if field not in rule_data:
                raise ValidationError(f"Missing required field: {field}")
    
    def _create_escalation_rule_record(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create escalation rule record in database."""
        # Placeholder - implement when escalation rule repository is available
        return {
            'id': 1,
            'name': rule_data['name'],
            'conditions': rule_data['conditions'],
            'actions': rule_data['actions'],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
