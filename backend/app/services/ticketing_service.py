"""
Comprehensive Ticketing Service Layer
Business logic for ISP customer support ticket management
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.auth.base import Administrator
from app.models.ticketing import (
    EscalationReason,
    FieldWorkOrder,
    FieldWorkStatus,
    KnowledgeBaseArticle,
    SLAPolicy,
    Ticket,
    TicketEscalation,
    TicketMessage,
    TicketPriority,
    TicketSource,
    TicketStatus,
    TicketStatusHistory,
    TicketType,
)
from app.services.webhook_integration_service import WebhookTriggers

logger = logging.getLogger(__name__)


class TicketService:
    """Core ticket management service"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.webhook_triggers = WebhookTriggers()

    def create_ticket(
        self, ticket_data: Dict[str, Any], created_by: int = None
    ) -> Ticket:
        """Create new support ticket"""
        try:
            # Generate unique ticket number
            ticket_number = self._generate_ticket_number()

            # Create ticket
            ticket = Ticket(
                ticket_number=ticket_number,
                ticket_type=TicketType(ticket_data["ticket_type"]),
                category=ticket_data.get("category"),
                subcategory=ticket_data.get("subcategory"),
                title=ticket_data["title"],
                description=ticket_data["description"],
                customer_id=ticket_data.get("customer_id"),
                service_id=ticket_data.get("service_id"),
                contact_id=ticket_data.get("contact_id"),
                priority=TicketPriority(ticket_data.get("priority", "normal")),
                urgency=ticket_data.get("urgency", 3),
                impact=ticket_data.get("impact", 3),
                source=TicketSource(ticket_data.get("source", "customer_portal")),
                source_reference=ticket_data.get("source_reference"),
                work_location=ticket_data.get("work_location"),
                gps_latitude=ticket_data.get("gps_latitude"),
                gps_longitude=ticket_data.get("gps_longitude"),
                tags=ticket_data.get("tags", []),
                custom_fields=ticket_data.get("custom_fields", {}),
                created_by=created_by,
            )

            # Apply SLA policy
            sla_policy = self._get_applicable_sla_policy(ticket)
            if sla_policy:
                ticket.sla_policy_id = sla_policy.id
                ticket.first_response_due = self._calculate_sla_due_date(
                    sla_policy.first_response_time
                )
                ticket.resolution_due = self._calculate_resolution_due_date(
                    ticket.priority, sla_policy
                )

            self.db.add(ticket)
            self.db.commit()
            self.db.refresh(ticket)

            # Create status history entry
            self._create_status_history(ticket.id, TicketStatus.NEW, created_by)

            # Auto-assign if rules exist
            self._auto_assign_ticket(ticket)

            # Trigger webhook event
            try:
                self.webhook_triggers.ticket_created(
                    {
                        "id": ticket.id,
                        "ticket_number": ticket.ticket_number,
                        "customer_id": ticket.customer_id,
                        "title": ticket.title,
                        "priority": ticket.priority.value,
                        "type": ticket.type.value,
                        "status": ticket.status.value,
                        "assigned_agent_id": ticket.assigned_agent_id,
                        "created_at": ticket.created_at.isoformat(),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to trigger ticket.created webhook: {e}")

            logger.info(
                f"Created ticket {ticket.ticket_number} for customer {ticket.customer_id}"
            )
            return ticket

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating ticket: {str(e)}")
            raise

    def update_ticket(
        self, ticket_id: int, update_data: Dict[str, Any], updated_by: int = None
    ) -> Ticket:
        """Update existing ticket"""
        try:
            ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not ticket:
                raise ValueError(f"Ticket {ticket_id} not found")

            # Update fields
            for field, value in update_data.items():
                if hasattr(ticket, field) and value is not None:
                    setattr(ticket, field, value)

            ticket.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(ticket)

            # Trigger webhook event
            try:
                self.webhook_triggers.ticket_updated(
                    {
                        "id": ticket.id,
                        "ticket_number": ticket.ticket_number,
                        "customer_id": ticket.customer_id,
                        "title": ticket.title,
                        "priority": ticket.priority.value,
                        "type": ticket.type.value,
                        "status": ticket.status.value,
                        "assigned_agent_id": ticket.assigned_agent_id,
                        "updated_at": ticket.updated_at.isoformat(),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to trigger ticket.updated webhook: {e}")

            logger.info(f"Updated ticket {ticket.ticket_number}")
            return ticket

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating ticket {ticket_id}: {str(e)}")
            raise

    def change_ticket_status(
        self,
        ticket_id: int,
        new_status: str,
        reason: str = None,
        changed_by: int = None,
    ) -> Ticket:
        """Change ticket status with history tracking"""
        try:
            ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not ticket:
                raise ValueError(f"Ticket {ticket_id} not found")

            old_status = ticket.status
            ticket.status = TicketStatus(new_status)
            ticket.updated_at = datetime.utcnow()

            # Set timestamps for specific status changes
            if new_status == "resolved":
                ticket.resolved_at = datetime.utcnow()
                ticket.resolution_sla_met = self._check_resolution_sla_met(ticket)
            elif new_status == "closed":
                ticket.closed_at = datetime.utcnow()

            self.db.commit()

            # Create status history
            self._create_status_history(
                ticket_id, TicketStatus(new_status), changed_by, reason
            )

            logger.info(
                f"Changed ticket {ticket.ticket_number} status from {old_status} to {new_status}"
            )
            return ticket

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error changing ticket status: {str(e)}")
            raise

    def assign_ticket(
        self,
        ticket_id: int,
        assigned_to: int,
        assigned_team: str = None,
        assigned_by: int = None,
    ) -> Ticket:
        """Assign ticket to agent/team"""
        try:
            ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not ticket:
                raise ValueError(f"Ticket {ticket_id} not found")

            ticket.assigned_to = assigned_to
            ticket.assigned_team = assigned_team
            ticket.assigned_at = datetime.utcnow()
            ticket.status = TicketStatus.ASSIGNED
            ticket.updated_at = datetime.utcnow()

            self.db.commit()

            # Create status history
            self._create_status_history(ticket_id, TicketStatus.ASSIGNED, assigned_by)

            logger.info(
                f"Assigned ticket {ticket.ticket_number} to agent {assigned_to}"
            )
            return ticket

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error assigning ticket: {str(e)}")
            raise

    def search_tickets(
        self, filters: Dict[str, Any], page: int = 1, per_page: int = 20
    ) -> Tuple[List[Ticket], int]:
        """Search tickets with filters and pagination"""
        try:
            query = self.db.query(Ticket)

            # Apply filters
            if filters.get("customer_id"):
                query = query.filter(Ticket.customer_id == filters["customer_id"])

            if filters.get("assigned_to"):
                query = query.filter(Ticket.assigned_to == filters["assigned_to"])

            if filters.get("status"):
                query = query.filter(Ticket.status == TicketStatus(filters["status"]))

            if filters.get("priority"):
                query = query.filter(
                    Ticket.priority == TicketPriority(filters["priority"])
                )

            if filters.get("ticket_type"):
                query = query.filter(
                    Ticket.ticket_type == TicketType(filters["ticket_type"])
                )

            if filters.get("category"):
                query = query.filter(Ticket.category == filters["category"])

            if filters.get("overdue"):
                now = datetime.utcnow()
                if filters["overdue"]:
                    query = query.filter(
                        or_(
                            and_(
                                Ticket.first_response_due < now,
                                Ticket.first_response_at.is_(None),
                            ),
                            and_(
                                Ticket.resolution_due < now,
                                Ticket.resolved_at.is_(None),
                            ),
                        )
                    )

            if filters.get("created_after"):
                query = query.filter(Ticket.created_at >= filters["created_after"])

            if filters.get("created_before"):
                query = query.filter(Ticket.created_at <= filters["created_before"])

            if filters.get("search_text"):
                search_term = f"%{filters['search_text']}%"
                query = query.filter(
                    or_(
                        Ticket.title.ilike(search_term),
                        Ticket.description.ilike(search_term),
                        Ticket.ticket_number.ilike(search_term),
                    )
                )

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            tickets = (
                query.order_by(desc(Ticket.created_at))
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )

            return tickets, total

        except Exception as e:
            logger.error(f"Error searching tickets: {str(e)}")
            raise

    def get_ticket_statistics(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get ticket statistics"""
        try:
            base_query = self.db.query(Ticket)

            # Apply filters if provided
            if filters:
                if filters.get("created_after"):
                    base_query = base_query.filter(
                        Ticket.created_at >= filters["created_after"]
                    )
                if filters.get("created_before"):
                    base_query = base_query.filter(
                        Ticket.created_at <= filters["created_before"]
                    )

            total_tickets = base_query.count()
            open_tickets = base_query.filter(
                Ticket.status.in_(
                    [TicketStatus.NEW, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS]
                )
            ).count()

            # Overdue tickets
            now = datetime.utcnow()
            overdue_tickets = base_query.filter(
                or_(
                    and_(
                        Ticket.first_response_due < now,
                        Ticket.first_response_at.is_(None),
                    ),
                    and_(Ticket.resolution_due < now, Ticket.resolved_at.is_(None)),
                )
            ).count()

            resolved_tickets = base_query.filter(
                Ticket.status == TicketStatus.RESOLVED
            ).count()

            # SLA performance
            sla_met_count = base_query.filter(
                and_(
                    Ticket.first_response_sla_met is True,
                    Ticket.resolution_sla_met is True,
                )
            ).count()

            sla_performance = {
                "total_with_sla": base_query.filter(
                    Ticket.sla_policy_id.isnot(None)
                ).count(),
                "sla_met": sla_met_count,
                "sla_percentage": (sla_met_count / max(total_tickets, 1)) * 100,
            }

            # Average response and resolution times
            response_times = (
                base_query.filter(Ticket.first_response_at.isnot(None))
                .with_entities(
                    func.avg(
                        func.extract(
                            "epoch", Ticket.first_response_at - Ticket.created_at
                        )
                        / 3600
                    )
                )
                .scalar()
                or 0
            )

            resolution_times = (
                base_query.filter(Ticket.resolved_at.isnot(None))
                .with_entities(
                    func.avg(
                        func.extract("epoch", Ticket.resolved_at - Ticket.created_at)
                        / 3600
                    )
                )
                .scalar()
                or 0
            )

            # Customer satisfaction
            satisfaction = (
                base_query.filter(Ticket.customer_satisfaction.isnot(None))
                .with_entities(func.avg(Ticket.customer_satisfaction))
                .scalar()
                or 0
            )

            return {
                "total_tickets": total_tickets,
                "open_tickets": open_tickets,
                "overdue_tickets": overdue_tickets,
                "resolved_tickets": resolved_tickets,
                "sla_performance": sla_performance,
                "average_response_time_hours": float(response_times),
                "average_resolution_time_hours": float(resolution_times),
                "customer_satisfaction": float(satisfaction),
            }

        except Exception as e:
            logger.error(f"Error getting ticket statistics: {str(e)}")
            raise

    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_part = secrets.token_hex(3).upper()
        return f"TK-{timestamp}-{random_part}"

    def _get_applicable_sla_policy(self, ticket: Ticket) -> Optional[SLAPolicy]:
        """Get applicable SLA policy for ticket"""
        # Simple implementation - get default policy
        return (
            self.db.query(SLAPolicy)
            .filter(SLAPolicy.is_default is True, SLAPolicy.is_active is True)
            .first()
        )

    def _calculate_sla_due_date(self, minutes: int) -> datetime:
        """Calculate SLA due date"""
        return datetime.utcnow() + timedelta(minutes=minutes)

    def _calculate_resolution_due_date(
        self, priority: TicketPriority, sla_policy: SLAPolicy
    ) -> datetime:
        """Calculate resolution due date based on priority"""
        minutes_map = {
            TicketPriority.CRITICAL: sla_policy.critical_resolution_time,
            TicketPriority.URGENT: sla_policy.urgent_resolution_time,
            TicketPriority.HIGH: sla_policy.high_resolution_time,
            TicketPriority.NORMAL: sla_policy.normal_resolution_time,
            TicketPriority.LOW: sla_policy.low_resolution_time,
        }
        return self._calculate_sla_due_date(
            minutes_map.get(priority, sla_policy.normal_resolution_time)
        )

    def _check_resolution_sla_met(self, ticket: Ticket) -> bool:
        """Check if resolution SLA was met"""
        if not ticket.resolution_due or not ticket.resolved_at:
            return False
        return ticket.resolved_at <= ticket.resolution_due

    def _create_status_history(
        self,
        ticket_id: int,
        status: TicketStatus,
        changed_by: int = None,
        reason: str = None,
    ):
        """Create status history entry"""
        history = TicketStatusHistory(
            ticket_id=ticket_id,
            status=status,
            changed_by=changed_by,
            change_reason=reason,
            changed_at=datetime.utcnow(),
        )
        self.db.add(history)
        self.db.commit()

    def _auto_assign_ticket(self, ticket: Ticket):
        """Auto-assign ticket based on rules"""
        # Simple implementation - could be enhanced with complex rules
        pass


class TicketMessageService:
    """Ticket message and communication service"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def add_message(
        self, ticket_id: int, message_data: Dict[str, Any]
    ) -> TicketMessage:
        """Add message to ticket"""
        try:
            message = TicketMessage(
                ticket_id=ticket_id,
                content=message_data["content"],
                message_type=message_data.get("message_type", "comment"),
                subject=message_data.get("subject"),
                content_format=message_data.get("content_format", "text"),
                is_internal=message_data.get("is_internal", False),
                is_solution=message_data.get("is_solution", False),
                author_type=message_data["author_type"],
                author_id=message_data.get("author_id"),
                author_name=message_data.get("author_name"),
                author_email=message_data.get("author_email"),
            )

            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            # Update ticket first response time if this is first agent response
            if message.author_type == "agent":
                self._update_first_response_time(ticket_id)

            logger.info(f"Added message to ticket {ticket_id}")
            return message

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding message: {str(e)}")
            raise

    def get_ticket_messages(
        self, ticket_id: int, page: int = 1, per_page: int = 20
    ) -> Tuple[List[TicketMessage], int]:
        """Get messages for ticket with pagination"""
        try:
            query = self.db.query(TicketMessage).filter(
                TicketMessage.ticket_id == ticket_id
            )

            total = query.count()
            messages = (
                query.order_by(asc(TicketMessage.created_at))
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )

            return messages, total

        except Exception as e:
            logger.error(f"Error getting ticket messages: {str(e)}")
            raise

    def _update_first_response_time(self, ticket_id: int):
        """Update first response time for ticket"""
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket and not ticket.first_response_at:
            ticket.first_response_at = datetime.utcnow()
            ticket.first_response_sla_met = (
                ticket.first_response_due is None
                or ticket.first_response_at <= ticket.first_response_due
            )
            self.db.commit()


class TicketEscalationService:
    """Ticket escalation management service"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def escalate_ticket(
        self, ticket_id: int, escalation_data: Dict[str, Any]
    ) -> TicketEscalation:
        """Escalate ticket to higher level"""
        try:
            escalation = TicketEscalation(
                ticket_id=ticket_id,
                escalation_reason=EscalationReason(
                    escalation_data["escalation_reason"]
                ),
                escalation_level=escalation_data.get("escalation_level", 1),
                escalated_to=escalation_data["escalated_to"],
                escalated_to_team=escalation_data.get("escalated_to_team"),
                escalation_notes=escalation_data.get("escalation_notes"),
                urgency_justification=escalation_data.get("urgency_justification"),
            )

            self.db.add(escalation)

            # Update ticket status and assignment
            ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                ticket.status = TicketStatus.ESCALATED
                ticket.assigned_to = escalation_data["escalated_to"]
                ticket.assigned_team = escalation_data.get("escalated_to_team")
                ticket.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(escalation)

            logger.info(
                f"Escalated ticket {ticket_id} to level {escalation.escalation_level}"
            )
            return escalation

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error escalating ticket: {str(e)}")
            raise


class FieldWorkService:
    """Field work order management service"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def create_field_work_order(
        self, ticket_id: int, work_data: Dict[str, Any]
    ) -> FieldWorkOrder:
        """Create field work order for ticket"""
        try:
            work_order_number = self._generate_work_order_number()

            field_work = FieldWorkOrder(
                ticket_id=ticket_id,
                work_order_number=work_order_number,
                work_type=work_data["work_type"],
                work_description=work_data["work_description"],
                special_instructions=work_data.get("special_instructions"),
                work_address=work_data["work_address"],
                gps_latitude=work_data.get("gps_latitude"),
                gps_longitude=work_data.get("gps_longitude"),
                location_contact_name=work_data.get("location_contact_name"),
                location_contact_phone=work_data.get("location_contact_phone"),
                priority=TicketPriority(work_data.get("priority", "normal")),
                scheduled_date=work_data.get("scheduled_date"),
                estimated_duration_hours=work_data.get("estimated_duration_hours"),
                assigned_technician=work_data.get("assigned_technician"),
                technician_team=work_data.get("technician_team"),
                required_equipment=work_data.get("required_equipment", []),
                required_materials=work_data.get("required_materials", []),
                customer_availability=work_data.get("customer_availability"),
                access_requirements=work_data.get("access_requirements"),
                safety_requirements=work_data.get("safety_requirements"),
            )

            self.db.add(field_work)
            self.db.commit()
            self.db.refresh(field_work)

            logger.info(
                f"Created field work order {work_order_number} for ticket {ticket_id}"
            )
            return field_work

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating field work order: {str(e)}")
            raise

    def update_field_work_status(
        self, work_order_id: int, status: str, update_data: Dict[str, Any] = None
    ) -> FieldWorkOrder:
        """Update field work order status"""
        try:
            field_work = (
                self.db.query(FieldWorkOrder)
                .filter(FieldWorkOrder.id == work_order_id)
                .first()
            )
            if not field_work:
                raise ValueError(f"Field work order {work_order_id} not found")

            field_work.status = FieldWorkStatus(status)
            field_work.updated_at = datetime.utcnow()

            if update_data:
                for field, value in update_data.items():
                    if hasattr(field_work, field) and value is not None:
                        setattr(field_work, field, value)

            # Set completion timestamp
            if status == "completed":
                field_work.completed_at = datetime.utcnow()
                field_work.work_completed = True

            self.db.commit()
            self.db.refresh(field_work)

            logger.info(
                f"Updated field work order {field_work.work_order_number} status to {status}"
            )
            return field_work

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating field work status: {str(e)}")
            raise

    def _generate_work_order_number(self) -> str:
        """Generate unique work order number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_part = secrets.token_hex(3).upper()
        return f"WO-{timestamp}-{random_part}"


class KnowledgeBaseService:
    """Knowledge base management service"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def create_article(
        self, article_data: Dict[str, Any], author_id: int
    ) -> KnowledgeBaseArticle:
        """Create knowledge base article"""
        try:
            article = KnowledgeBaseArticle(
                title=article_data["title"],
                summary=article_data.get("summary"),
                content=article_data["content"],
                content_format=article_data.get("content_format", "html"),
                category=article_data.get("category"),
                subcategory=article_data.get("subcategory"),
                tags=article_data.get("tags", []),
                keywords=article_data.get("keywords", []),
                ticket_types=article_data.get("ticket_types", []),
                service_types=article_data.get("service_types", []),
                difficulty_level=article_data.get("difficulty_level"),
                is_public=article_data.get("is_public", False),
                author_id=author_id,
                version="1.0",
            )

            self.db.add(article)
            self.db.commit()
            self.db.refresh(article)

            logger.info(f"Created knowledge base article: {article.title}")
            return article

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating knowledge base article: {str(e)}")
            raise

    def search_articles(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[KnowledgeBaseArticle], int]:
        """Search knowledge base articles"""
        try:
            db_query = self.db.query(KnowledgeBaseArticle).filter(
                KnowledgeBaseArticle.status == "published"
            )

            # Text search
            if query:
                search_term = f"%{query}%"
                db_query = db_query.filter(
                    or_(
                        KnowledgeBaseArticle.title.ilike(search_term),
                        KnowledgeBaseArticle.summary.ilike(search_term),
                        KnowledgeBaseArticle.content.ilike(search_term),
                    )
                )

            # Apply filters
            if filters:
                if filters.get("category"):
                    db_query = db_query.filter(
                        KnowledgeBaseArticle.category == filters["category"]
                    )

                if filters.get("is_public") is not None:
                    db_query = db_query.filter(
                        KnowledgeBaseArticle.is_public == filters["is_public"]
                    )

            total = db_query.count()
            articles = (
                db_query.order_by(desc(KnowledgeBaseArticle.view_count))
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )

            return articles, total

        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            raise

    def update_ticket_status(
        self, ticket_id: int, new_status: str, changed_by: int, reason: str = None
    ) -> bool:
        """Update ticket status with history tracking"""
        try:
            ticket = self.db.query(Ticket).filter_by(id=ticket_id).first()
            if not ticket:
                return False

            old_status = ticket.status
            ticket.status = TicketStatus(new_status)

            # Update timestamps
            if new_status == "resolved":
                ticket.resolved_at = datetime.now()
            elif new_status == "closed":
                ticket.closed_at = datetime.now()

            # Create status history
            self._create_status_history(
                ticket_id,
                old_status,
                ticket.status,
                reason or f"Status changed to {new_status}",
                changed_by,
                "manual",
            )

            # Add automation event
            ticket.add_automation_event(
                "status_changed",
                f"Status changed from {old_status.value} to {new_status}",
                changed_by,
            )

            self.db.commit()

            # Send notifications
            self._send_status_change_notifications(ticket, old_status)

            logger.info(f"Updated ticket {ticket.ticket_number} status to {new_status}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating ticket status: {e}")
            return False

    def assign_ticket(
        self, ticket_id: int, assigned_to: int, assigned_by: int, team: str = None
    ) -> bool:
        """Assign ticket to agent/team"""
        try:
            ticket = self.db.query(Ticket).filter_by(id=ticket_id).first()
            if not ticket:
                return False

            old_assignee = ticket.assigned_to
            ticket.assigned_to = assigned_to
            ticket.assigned_team = team
            ticket.assigned_at = datetime.now()

            # Update status if new
            if ticket.status == TicketStatus.NEW:
                ticket.status = TicketStatus.ASSIGNED

            # Create status history
            self._create_status_history(
                ticket_id,
                ticket.status,
                ticket.status,
                f"Assigned to {self._get_agent_name(assigned_to)}",
                assigned_by,
                "manual",
            )

            # Add automation event
            ticket.add_automation_event(
                "ticket_assigned",
                f"Assigned to {self._get_agent_name(assigned_to)}",
                assigned_by,
            )

            self.db.commit()

            # Send notifications
            self._send_assignment_notifications(ticket, old_assignee)

            logger.info(
                f"Assigned ticket {ticket.ticket_number} to agent {assigned_to}"
            )
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error assigning ticket: {e}")
            return False

    def add_message(
        self, ticket_id: int, message_data: Dict[str, Any]
    ) -> TicketMessage:
        """Add message to ticket"""
        try:
            message = TicketMessage(
                ticket_id=ticket_id,
                message_type=message_data.get("message_type", "comment"),
                subject=message_data.get("subject"),
                content=message_data["content"],
                content_format=message_data.get("content_format", "text"),
                author_type=message_data["author_type"],
                author_id=message_data.get("author_id"),
                author_name=message_data.get("author_name"),
                author_email=message_data.get("author_email"),
                is_internal=message_data.get("is_internal", False),
                is_solution=message_data.get("is_solution", False),
                is_auto_generated=message_data.get("is_auto_generated", False),
            )

            self.db.add(message)
            self.db.flush()

            # Update ticket first response if this is first agent response
            ticket = self.db.query(Ticket).filter_by(id=ticket_id).first()
            if (
                ticket
                and not ticket.first_response_at
                and message.author_type == "agent"
                and not message.is_internal
            ):
                ticket.first_response_at = datetime.now()
                ticket.first_response_sla_met = self._check_first_response_sla(ticket)

            self.db.commit()

            # Send notifications
            self._send_message_notifications(message)

            logger.info(f"Added message to ticket {ticket.ticket_number}")
            return message

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding message: {e}")
            raise

    def escalate_ticket(
        self, ticket_id: int, escalation_data: Dict[str, Any]
    ) -> TicketEscalation:
        """Escalate ticket to higher level"""
        try:
            escalation = TicketEscalation(
                ticket_id=ticket_id,
                escalation_reason=EscalationReason(escalation_data["reason"]),
                escalation_level=escalation_data.get("level", 1),
                escalated_from=escalation_data.get("escalated_from"),
                escalated_to=escalation_data["escalated_to"],
                escalated_from_team=escalation_data.get("escalated_from_team"),
                escalated_to_team=escalation_data.get("escalated_to_team"),
                escalation_notes=escalation_data.get("notes"),
                urgency_justification=escalation_data.get("urgency_justification"),
            )

            self.db.add(escalation)
            self.db.flush()

            # Update ticket
            ticket = self.db.query(Ticket).filter_by(id=ticket_id).first()
            if ticket:
                ticket.status = TicketStatus.ESCALATED
                ticket.assigned_to = escalation_data["escalated_to"]
                ticket.assigned_team = escalation_data.get("escalated_to_team")

                # Increase priority if not already at max
                if ticket.priority != TicketPriority.CRITICAL:
                    if ticket.priority == TicketPriority.LOW:
                        ticket.priority = TicketPriority.NORMAL
                    elif ticket.priority == TicketPriority.NORMAL:
                        ticket.priority = TicketPriority.HIGH
                    elif ticket.priority == TicketPriority.HIGH:
                        ticket.priority = TicketPriority.URGENT
                    elif ticket.priority == TicketPriority.URGENT:
                        ticket.priority = TicketPriority.CRITICAL

                # Add automation event
                ticket.add_automation_event(
                    "ticket_escalated",
                    f'Escalated due to {escalation_data["reason"]}',
                    escalation_data.get("escalated_from"),
                )

            self.db.commit()

            # Send notifications
            self._send_escalation_notifications(escalation)

            logger.info(f"Escalated ticket {ticket.ticket_number}")
            return escalation

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error escalating ticket: {e}")
            raise

    def get_tickets(
        self, filters: Dict[str, Any] = None, limit: int = 50, offset: int = 0
    ) -> List[Ticket]:
        """Get tickets with filtering and pagination"""
        try:
            query = self.db.query(Ticket)

            if filters:
                if "customer_id" in filters:
                    query = query.filter(Ticket.customer_id == filters["customer_id"])
                if "assigned_to" in filters:
                    query = query.filter(Ticket.assigned_to == filters["assigned_to"])
                if "status" in filters:
                    query = query.filter(Ticket.status == filters["status"])
                if "priority" in filters:
                    query = query.filter(Ticket.priority == filters["priority"])
                if "ticket_type" in filters:
                    query = query.filter(Ticket.ticket_type == filters["ticket_type"])
                if "category" in filters:
                    query = query.filter(Ticket.category == filters["category"])
                if "overdue" in filters and filters["overdue"]:
                    query = query.filter(
                        Ticket.due_date < datetime.now(),
                        Ticket.status.in_(
                            [
                                TicketStatus.NEW,
                                TicketStatus.ASSIGNED,
                                TicketStatus.IN_PROGRESS,
                            ]
                        ),
                    )
                if "created_after" in filters:
                    query = query.filter(Ticket.created_at >= filters["created_after"])
                if "created_before" in filters:
                    query = query.filter(Ticket.created_at <= filters["created_before"])

            tickets = (
                query.order_by(desc(Ticket.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )

            return tickets

        except Exception as e:
            logger.error(f"Error getting tickets: {e}")
            return []

    def get_ticket_statistics(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get ticket statistics and metrics"""
        try:
            base_query = self.db.query(Ticket)

            if filters:
                if "date_from" in filters:
                    base_query = base_query.filter(
                        Ticket.created_at >= filters["date_from"]
                    )
                if "date_to" in filters:
                    base_query = base_query.filter(
                        Ticket.created_at <= filters["date_to"]
                    )
                if "assigned_to" in filters:
                    base_query = base_query.filter(
                        Ticket.assigned_to == filters["assigned_to"]
                    )

            # Basic counts
            total_tickets = base_query.count()
            open_tickets = base_query.filter(
                Ticket.status.in_(
                    [TicketStatus.NEW, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS]
                )
            ).count()

            overdue_tickets = base_query.filter(
                Ticket.due_date < datetime.now(),
                Ticket.status.in_(
                    [TicketStatus.NEW, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS]
                ),
            ).count()

            # SLA performance
            sla_met_count = base_query.filter(Ticket.resolution_sla_met is True).count()

            resolved_tickets = base_query.filter(
                Ticket.status == TicketStatus.RESOLVED
            ).count()

            # Average response and resolution times
            avg_response_time = (
                self.db.query(
                    func.avg(
                        func.extract(
                            "epoch", Ticket.first_response_at - Ticket.created_at
                        )
                        / 3600
                    )
                )
                .filter(Ticket.first_response_at.isnot(None))
                .scalar()
                or 0
            )

            avg_resolution_time = (
                self.db.query(
                    func.avg(
                        func.extract("epoch", Ticket.resolved_at - Ticket.created_at)
                        / 3600
                    )
                )
                .filter(Ticket.resolved_at.isnot(None))
                .scalar()
                or 0
            )

            # Customer satisfaction
            avg_satisfaction = (
                self.db.query(func.avg(Ticket.customer_satisfaction))
                .filter(Ticket.customer_satisfaction.isnot(None))
                .scalar()
                or 0
            )

            return {
                "total_tickets": total_tickets,
                "open_tickets": open_tickets,
                "overdue_tickets": overdue_tickets,
                "resolved_tickets": resolved_tickets,
                "sla_performance": {
                    "met_count": sla_met_count,
                    "total_with_sla": resolved_tickets,
                    "percentage": round(
                        (
                            (sla_met_count / resolved_tickets * 100)
                            if resolved_tickets > 0
                            else 0
                        ),
                        1,
                    ),
                },
                "average_response_time_hours": round(avg_response_time, 2),
                "average_resolution_time_hours": round(avg_resolution_time, 2),
                "customer_satisfaction": round(avg_satisfaction, 1),
            }

        except Exception as e:
            logger.error(f"Error getting ticket statistics: {e}")
            return {}

    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number"""
        prefix = "TKT"
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = secrets.token_hex(3).upper()
        return f"{prefix}-{timestamp}-{random_suffix}"

    def _get_sla_policy_for_ticket(self, ticket: Ticket) -> Optional[SLAPolicy]:
        """Get applicable SLA policy for ticket"""
        try:
            # Get default SLA policy for now
            sla_policy = (
                self.db.query(SLAPolicy)
                .filter(SLAPolicy.is_default is True, SLAPolicy.is_active is True)
                .first()
            )

            if not sla_policy:
                # Get any active SLA policy
                sla_policy = (
                    self.db.query(SLAPolicy).filter(SLAPolicy.is_active is True).first()
                )

            return sla_policy

        except Exception as e:
            logger.error(f"Error getting SLA policy: {e}")
            return None

    def _calculate_due_date(self, ticket: Ticket, sla_policy: SLAPolicy) -> datetime:
        """Calculate ticket due date based on SLA policy"""
        resolution_time = sla_policy.get_resolution_time_for_priority(ticket.priority)
        return ticket.created_at + timedelta(minutes=resolution_time)

    def _calculate_first_response_due(
        self, ticket: Ticket, sla_policy: SLAPolicy
    ) -> datetime:
        """Calculate first response due date"""
        return ticket.created_at + timedelta(minutes=sla_policy.first_response_time)

    def _auto_assign_ticket(self, ticket: Ticket):
        """Auto-assign ticket based on rules"""
        # Simple round-robin assignment for now
        try:
            if ticket.ticket_type == TicketType.TECHNICAL:
                ticket.assigned_team = "technical"
                # Get next available technical agent
                tech_agent = (
                    self.db.query(Administrator)
                    .filter(Administrator.role == "technical")
                    .first()
                )
                if tech_agent:
                    ticket.assigned_to = tech_agent.id
                    ticket.assigned_at = datetime.now()
            elif ticket.ticket_type == TicketType.SUPPORT:
                ticket.assigned_team = "support"
                # Get next available support agent
                support_agent = (
                    self.db.query(Administrator)
                    .filter(Administrator.role == "support")
                    .first()
                )
                if support_agent:
                    ticket.assigned_to = support_agent.id
                    ticket.assigned_at = datetime.now()

        except Exception as e:
            logger.error(f"Error auto-assigning ticket: {e}")

    def _apply_ticket_business_rules(self, ticket: Ticket):
        """Apply business rules to ticket"""
        # Implement custom business rules here
        pass

    def _create_status_history(
        self,
        ticket_id: int,
        previous_status,
        new_status,
        reason: str,
        changed_by: int,
        method: str,
    ):
        """Create status history record"""
        try:
            history = TicketStatusHistory(
                ticket_id=ticket_id,
                previous_status=previous_status.value if previous_status else None,
                new_status=new_status.value,
                change_reason=reason,
                changed_by=changed_by,
                change_method=method,
            )
            self.db.add(history)

        except Exception as e:
            logger.error(f"Error creating status history: {e}")

    def _get_agent_name(self, agent_id: int) -> str:
        """Get agent name by ID"""
        try:
            agent = self.db.query(Administrator).filter_by(id=agent_id).first()
            return agent.username if agent else f"Agent {agent_id}"
        except Exception:
            return f"Agent {agent_id}"

    def _check_first_response_sla(self, ticket: Ticket) -> bool:
        """Check if first response SLA was met"""
        if not ticket.first_response_due or not ticket.first_response_at:
            return False
        return ticket.first_response_at <= ticket.first_response_due

    def _send_ticket_created_notifications(self, ticket: Ticket):
        """Send notifications for ticket creation"""
        # Implement notification logic
        pass

    def _send_status_change_notifications(self, ticket: Ticket, old_status):
        """Send notifications for status changes"""
        # Implement notification logic
        pass

    def _send_assignment_notifications(self, ticket: Ticket, old_assignee):
        """Send notifications for ticket assignment"""
        # Implement notification logic
        pass

    def _send_message_notifications(self, message: TicketMessage):
        """Send notifications for new messages"""
        # Implement notification logic
        pass

    def _send_escalation_notifications(self, escalation: TicketEscalation):
        """Send notifications for escalations"""
        # Implement notification logic
        pass


# Duplicate class definitions removed to fix F811 redefinition errors
# FieldWorkService and KnowledgeBaseService are already implemented above
