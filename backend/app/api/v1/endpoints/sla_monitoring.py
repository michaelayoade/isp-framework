"""
SLA Monitoring API Endpoints

Provides REST API endpoints for SLA monitoring and escalation including:
- SLA breach detection and reporting
- Escalation queue management
- SLA performance metrics and analytics
- Escalation rule configuration
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.models.auth import Administrator
from app.schemas.sla_monitoring import (
    SLABreachReport, SLAPerformanceMetrics, EscalationQueueEntry,
    EscalationRule, EscalationRuleCreate, EscalationRuleUpdate
)
from app.services.sla_monitoring import SLAMonitoringService
from app.core.exceptions import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sla/check-breaches", response_model=dict)
async def check_sla_breaches(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Check for SLA breaches and mark tickets accordingly."""
    sla_service = SLAMonitoringService(db)
    
    try:
        result = sla_service.check_sla_breaches()
        logger.info(f"Admin {current_admin.username} triggered SLA breach check")
        return result
    except Exception as e:
        logger.error(f"Error checking SLA breaches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check SLA breaches"
        )


@router.post("/escalation/process-queue", response_model=dict)
async def process_escalation_queue(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Process tickets in the escalation queue."""
    sla_service = SLAMonitoringService(db)
    
    try:
        result = sla_service.process_escalation_queue()
        logger.info(f"Admin {current_admin.username} triggered escalation queue processing")
        return result
    except Exception as e:
        logger.error(f"Error processing escalation queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process escalation queue"
        )


@router.get("/sla/performance-metrics", response_model=dict)
async def get_sla_performance_metrics(
    period_days: int = Query(30, ge=1, le=365, description="Period in days for metrics calculation"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get SLA performance metrics for a given period."""
    sla_service = SLAMonitoringService(db)
    
    try:
        metrics = sla_service.get_sla_performance_metrics(period_days)
        return metrics
    except Exception as e:
        logger.error(f"Error retrieving SLA performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SLA performance metrics"
        )


@router.get("/escalation/queue", response_model=dict)
async def get_escalation_queue(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get current escalation queue with pagination."""
    sla_service = SLAMonitoringService(db)
    
    try:
        queue = sla_service.get_escalation_queue(page, per_page)
        return queue
    except Exception as e:
        logger.error(f"Error retrieving escalation queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve escalation queue"
        )


@router.post("/escalation/rules", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_escalation_rule(
    rule_data: dict,  # Using dict for now, replace with proper schema when available
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new escalation rule."""
    sla_service = SLAMonitoringService(db)
    
    try:
        rule = sla_service.create_escalation_rule(rule_data)
        logger.info(f"Admin {current_admin.username} created escalation rule {rule['id']}")
        return rule
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating escalation rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create escalation rule"
        )


@router.get("/sla/dashboard", response_model=dict)
async def get_sla_dashboard(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive SLA dashboard data."""
    sla_service = SLAMonitoringService(db)
    
    try:
        # Get current metrics
        metrics = sla_service.get_sla_performance_metrics(30)
        
        # Get escalation queue summary
        queue = sla_service.get_escalation_queue(1, 10)
        
        # Combine dashboard data
        dashboard = {
            'sla_metrics': metrics,
            'escalation_queue_summary': {
                'total_entries': queue['total'],
                'recent_entries': queue['entries'][:5]  # Show top 5
            },
            'alerts': {
                'breached_tickets_today': 0,  # Placeholder
                'approaching_breach': 0,      # Placeholder
                'escalations_pending': queue['total']
            },
            'last_updated': metrics.get('period_end')
        }
        
        return dashboard
    except Exception as e:
        logger.error(f"Error retrieving SLA dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SLA dashboard"
        )


@router.get("/sla/tickets/{ticket_id}/status", response_model=dict)
async def get_ticket_sla_status(
    ticket_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get SLA status for a specific ticket."""
    sla_service = SLAMonitoringService(db)
    
    try:
        # This would need to be implemented in the service layer
        # For now, return a placeholder response
        return {
            'ticket_id': ticket_id,
            'sla_status': 'within_sla',
            'time_remaining_minutes': 120,
            'elapsed_minutes': 60,
            'sla_target_minutes': 240,
            'breach_risk': 'low'
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving ticket SLA status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket SLA status"
        )


@router.post("/tickets/{ticket_id}/escalate", response_model=dict)
async def manual_escalate_ticket(
    ticket_id: int,
    reason: str = Query(..., description="Reason for manual escalation"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Manually escalate a ticket."""
    sla_service = SLAMonitoringService(db)
    
    try:
        # This would need to be implemented in the service layer
        # For now, return a placeholder response
        result = {
            'ticket_id': ticket_id,
            'escalated_by': current_admin.id,
            'reason': reason,
            'old_assignee': None,
            'new_assignee': None,
            'escalation_level': 1,
            'escalated_at': '2025-01-29T10:30:00Z'
        }
        
        logger.info(f"Admin {current_admin.username} manually escalated ticket {ticket_id}")
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error escalating ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to escalate ticket"
        )
