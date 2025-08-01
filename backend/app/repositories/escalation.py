"""
Escalation Repository Layer

Comprehensive repository layer for ticket escalation management including:
- Escalation queue management
- Escalation rule processing
- Escalation analytics and reporting
- SLA breach detection
- Automated escalation workflows
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.ticketing.escalation import EscalationReason, TicketEscalation
from app.models.ticketing.ticket import Ticket
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class EscalationQueueRepository(BaseRepository[TicketEscalation]):
    """Repository for escalation queue management"""

    def __init__(self, db: Session):
        super().__init__(db, TicketEscalation)

    def create_escalation(
        self,
        ticket_id: int,
        escalation_reason: EscalationReason,
        escalated_from: Optional[int] = None,
        escalated_to: Optional[int] = None,
        escalated_from_team: Optional[str] = None,
        escalated_to_team: Optional[str] = None,
        escalation_notes: Optional[str] = None,
        urgency_justification: Optional[str] = None,
        escalation_level: int = 1,
    ) -> TicketEscalation:
        """Create a new ticket escalation"""
        
        escalation = TicketEscalation(
            ticket_id=ticket_id,
            escalation_reason=escalation_reason,
            escalation_level=escalation_level,
            escalated_from=escalated_from,
            escalated_to=escalated_to,
            escalated_from_team=escalated_from_team,
            escalated_to_team=escalated_to_team,
            escalation_notes=escalation_notes,
            urgency_justification=urgency_justification,
        )
        
        self.db.add(escalation)
        self.db.commit()
        self.db.refresh(escalation)
        
        logger.info(f"Created escalation for ticket {ticket_id}: {escalation_reason.value}")
        return escalation

    def get_active_escalations(
        self,
        escalated_to: Optional[int] = None,
        escalated_to_team: Optional[str] = None,
        escalation_level: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TicketEscalation]:
        """Get active escalations with filtering"""
        
        query = (
            self.db.query(TicketEscalation)
            .options(
                joinedload(TicketEscalation.ticket),
                joinedload(TicketEscalation.escalator),
                joinedload(TicketEscalation.escalatee),
            )
            .filter(TicketEscalation.is_active == True)
        )
        
        if escalated_to:
            query = query.filter(TicketEscalation.escalated_to == escalated_to)
        
        if escalated_to_team:
            query = query.filter(TicketEscalation.escalated_to_team == escalated_to_team)
        
        if escalation_level:
            query = query.filter(TicketEscalation.escalation_level == escalation_level)
        
        return (
            query.order_by(desc(TicketEscalation.escalated_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def respond_to_escalation(
        self,
        escalation_id: int,
        responded_by: int,
        response_action: str,
        response_notes: Optional[str] = None,
    ) -> TicketEscalation:
        """Respond to an escalation"""
        
        escalation = self.get_by_id(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")
        
        escalation.responded_by = responded_by
        escalation.response_action = response_action
        escalation.response_notes = response_notes
        escalation.responded_at = datetime.now(timezone.utc)
        escalation.is_active = False
        
        self.db.commit()
        self.db.refresh(escalation)
        
        logger.info(f"Escalation {escalation_id} responded to: {response_action}")
        return escalation

    def get_escalation_history(
        self,
        ticket_id: int,
    ) -> List[TicketEscalation]:
        """Get complete escalation history for a ticket"""
        
        return (
            self.db.query(TicketEscalation)
            .options(
                joinedload(TicketEscalation.escalator),
                joinedload(TicketEscalation.escalatee),
                joinedload(TicketEscalation.responder),
            )
            .filter(TicketEscalation.ticket_id == ticket_id)
            .order_by(desc(TicketEscalation.escalated_at))
            .all()
        )

    def get_escalation_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        escalated_to: Optional[int] = None,
        escalated_to_team: Optional[str] = None,
    ) -> Dict:
        """Get escalation statistics"""
        
        query = self.db.query(TicketEscalation)
        
        if start_date:
            query = query.filter(TicketEscalation.escalated_at >= start_date)
        
        if end_date:
            query = query.filter(TicketEscalation.escalated_at <= end_date)
        
        if escalated_to:
            query = query.filter(TicketEscalation.escalated_to == escalated_to)
        
        if escalated_to_team:
            query = query.filter(TicketEscalation.escalated_to_team == escalated_to_team)
        
        total_escalations = query.count()
        active_escalations = query.filter(TicketEscalation.is_active == True).count()
        responded_escalations = query.filter(TicketEscalation.is_active == False).count()
        
        # Average response time for responded escalations
        avg_response_time = None
        if responded_escalations > 0:
            response_times = (
                query.filter(TicketEscalation.is_active == False)
                .filter(TicketEscalation.responded_at.isnot(None))
                .with_entities(
                    func.extract(
                        'epoch',
                        TicketEscalation.responded_at - TicketEscalation.escalated_at
                    ).label('response_time')
                )
                .all()
            )
            
            if response_times:
                avg_response_time = sum(rt.response_time for rt in response_times) / len(response_times)
        
        # Escalation reasons breakdown
        reason_breakdown = (
            query.with_entities(
                TicketEscalation.escalation_reason,
                func.count(TicketEscalation.id).label('count')
            )
            .group_by(TicketEscalation.escalation_reason)
            .all()
        )
        
        return {
            "total_escalations": total_escalations,
            "active_escalations": active_escalations,
            "responded_escalations": responded_escalations,
            "average_response_time_seconds": avg_response_time,
            "escalation_reasons": {
                reason.escalation_reason.value: reason.count
                for reason in reason_breakdown
            },
        }

    def get_overdue_escalations(
        self,
        hours_threshold: int = 24,
    ) -> List[TicketEscalation]:
        """Get escalations that are overdue for response"""
        
        threshold_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
        
        return (
            self.db.query(TicketEscalation)
            .options(
                joinedload(TicketEscalation.ticket),
                joinedload(TicketEscalation.escalatee),
            )
            .filter(TicketEscalation.is_active == True)
            .filter(TicketEscalation.escalated_at <= threshold_time)
            .order_by(TicketEscalation.escalated_at)
            .all()
        )


class EscalationRuleRepository(BaseRepository):
    """Repository for escalation rule processing and automation"""

    def __init__(self, db: Session):
        self.db = db

    def check_sla_breaches(
        self,
        sla_hours: int = 24,
    ) -> List[Ticket]:
        """Find tickets that have breached SLA and need escalation"""
        
        threshold_time = datetime.now(timezone.utc) - timedelta(hours=sla_hours)
        
        # Find tickets that are open and past SLA without escalation
        tickets_needing_escalation = (
            self.db.query(Ticket)
            .outerjoin(TicketEscalation)
            .filter(Ticket.status.in_(["open", "in_progress"]))
            .filter(Ticket.created_at <= threshold_time)
            .filter(TicketEscalation.id.is_(None))  # No existing escalations
            .all()
        )
        
        return tickets_needing_escalation

    def auto_escalate_sla_breaches(
        self,
        escalated_to_team: str = "management",
        sla_hours: int = 24,
    ) -> List[TicketEscalation]:
        """Automatically escalate tickets that have breached SLA"""
        
        tickets_to_escalate = self.check_sla_breaches(sla_hours)
        escalations_created = []
        
        escalation_repo = EscalationQueueRepository(self.db)
        
        for ticket in tickets_to_escalate:
            try:
                escalation = escalation_repo.create_escalation(
                    ticket_id=ticket.id,
                    escalation_reason=EscalationReason.SLA_BREACH,
                    escalated_to_team=escalated_to_team,
                    escalation_notes=f"Automatic escalation due to SLA breach ({sla_hours}h)",
                    urgency_justification=f"Ticket has been open for more than {sla_hours} hours",
                )
                escalations_created.append(escalation)
                
            except Exception as e:
                logger.error(f"Failed to auto-escalate ticket {ticket.id}: {e}")
        
        logger.info(f"Auto-escalated {len(escalations_created)} tickets for SLA breach")
        return escalations_created

    def check_repeated_issues(
        self,
        customer_id: int,
        days_lookback: int = 30,
        min_tickets: int = 3,
    ) -> List[Ticket]:
        """Find customers with repeated issues that may need escalation"""
        
        threshold_date = datetime.now(timezone.utc) - timedelta(days=days_lookback)
        
        # Count tickets per customer in the lookback period
        ticket_counts = (
            self.db.query(
                Ticket.customer_id,
                func.count(Ticket.id).label('ticket_count')
            )
            .filter(Ticket.created_at >= threshold_date)
            .filter(Ticket.customer_id == customer_id)
            .group_by(Ticket.customer_id)
            .having(func.count(Ticket.id) >= min_tickets)
            .all()
        )
        
        if not ticket_counts:
            return []
        
        # Get the actual tickets for escalation consideration
        recent_tickets = (
            self.db.query(Ticket)
            .filter(Ticket.customer_id == customer_id)
            .filter(Ticket.created_at >= threshold_date)
            .filter(Ticket.status.in_(["open", "in_progress"]))
            .order_by(desc(Ticket.created_at))
            .all()
        )
        
        return recent_tickets

    def escalate_complex_tickets(
        self,
        complexity_keywords: List[str] = None,
        escalated_to_team: str = "senior_support",
    ) -> List[TicketEscalation]:
        """Escalate tickets based on complexity indicators"""
        
        if not complexity_keywords:
            complexity_keywords = [
                "integration", "api", "database", "server", "network",
                "configuration", "custom", "advanced", "technical"
            ]
        
        # Find tickets with complexity indicators in title or description
        complex_tickets = []
        for keyword in complexity_keywords:
            tickets = (
                self.db.query(Ticket)
                .outerjoin(TicketEscalation)
                .filter(Ticket.status.in_(["open", "in_progress"]))
                .filter(
                    or_(
                        Ticket.title.ilike(f"%{keyword}%"),
                        Ticket.description.ilike(f"%{keyword}%")
                    )
                )
                .filter(TicketEscalation.id.is_(None))  # No existing escalations
                .all()
            )
            complex_tickets.extend(tickets)
        
        # Remove duplicates
        complex_tickets = list(set(complex_tickets))
        
        escalations_created = []
        escalation_repo = EscalationQueueRepository(self.db)
        
        for ticket in complex_tickets:
            try:
                escalation = escalation_repo.create_escalation(
                    ticket_id=ticket.id,
                    escalation_reason=EscalationReason.COMPLEXITY,
                    escalated_to_team=escalated_to_team,
                    escalation_notes="Automatic escalation due to complexity indicators",
                    urgency_justification="Ticket contains technical complexity keywords",
                )
                escalations_created.append(escalation)
                
            except Exception as e:
                logger.error(f"Failed to escalate complex ticket {ticket.id}: {e}")
        
        logger.info(f"Escalated {len(escalations_created)} complex tickets")
        return escalations_created
