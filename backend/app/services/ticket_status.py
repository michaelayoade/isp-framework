from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.ticket.status import TicketStatus
from app.schemas.ticket_status import TicketStatusCreate, TicketStatusUpdate
from app.core.exceptions import NotFoundError, DuplicateError, ValidationError
import logging

logger = logging.getLogger(__name__)


class TicketStatusService:
    """Service layer for ticket status management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_ticket_statuses(self, active_only: bool = True) -> List[TicketStatus]:
        """List all ticket statuses, optionally filtering by active status."""
        query = self.db.query(TicketStatus)
        
        if active_only:
            query = query.filter(TicketStatus.is_active == True)
        
        statuses = query.order_by(TicketStatus.sort_order, TicketStatus.name).all()
        return statuses
    
    def get_ticket_status(self, status_id: int) -> TicketStatus:
        """Get a ticket status by ID."""
        status = self.db.query(TicketStatus).filter(TicketStatus.id == status_id).first()
        if not status:
            raise NotFoundError(f"Ticket status with ID {status_id} not found")
        return status
    
    def get_ticket_status_by_code(self, code: str) -> Optional[TicketStatus]:
        """Get a ticket status by code."""
        return self.db.query(TicketStatus).filter(TicketStatus.code == code).first()
    
    def create_ticket_status(self, status_data: TicketStatusCreate) -> TicketStatus:
        """Create a new ticket status."""
        # Check if code already exists
        existing = self.get_ticket_status_by_code(status_data.code)
        if existing:
            raise DuplicateError(f"Ticket status with code '{status_data.code}' already exists")
        
        # Create status
        status_dict = status_data.model_dump()
        status_dict['is_system'] = False  # User-created statuses are not system statuses
        
        status = TicketStatus(**status_dict)
        self.db.add(status)
        self.db.commit()
        self.db.refresh(status)
        
        logger.info(f"Created ticket status: {status.code}")
        return status
    
    def update_ticket_status(self, status_id: int, status_data: TicketStatusUpdate) -> TicketStatus:
        """Update an existing ticket status."""
        status = self.get_ticket_status(status_id)
        
        # Check if code is being changed and if it conflicts
        if status_data.code and status_data.code != status.code:
            existing = self.get_ticket_status_by_code(status_data.code)
            if existing:
                raise DuplicateError(f"Ticket status with code '{status_data.code}' already exists")
        
        # Update fields
        update_data = status_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(status, field, value)
        
        status.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(status)
        
        logger.info(f"Updated ticket status {status_id}")
        return status
    
    def delete_ticket_status(self, status_id: int):
        """Delete a ticket status (only non-system statuses)."""
        status = self.get_ticket_status(status_id)
        
        # Check if it's a system status
        if status.is_system:
            raise ValidationError(f"System ticket status '{status.code}' cannot be deleted")
        
        # Check if it's in use
        try:
            from app.models.ticket.base import Ticket
            tickets_using_status = self.db.query(Ticket).filter(
                Ticket.status_id == status_id
            ).count()
            
            if tickets_using_status > 0:
                raise ValidationError(f"Ticket status '{status.code}' is in use by {tickets_using_status} tickets and cannot be deleted")
        except ImportError:
            # Ticket model doesn't exist yet, skip this check
            pass
        
        self.db.delete(status)
        self.db.commit()
        
        logger.info(f"Deleted ticket status {status_id}")
    
    def get_initial_ticket_status(self) -> TicketStatus:
        """Get the initial ticket status for new tickets."""
        initial_status = self.db.query(TicketStatus).filter(
            TicketStatus.is_initial == True,
            TicketStatus.is_active == True
        ).first()
        
        if not initial_status:
            # Fallback to 'open' status
            initial_status = self.get_ticket_status_by_code('open')
            
            if not initial_status:
                raise ValidationError("No initial ticket status found")
        
        return initial_status
    
    def get_final_ticket_statuses(self) -> List[TicketStatus]:
        """Get all final ticket statuses."""
        return self.db.query(TicketStatus).filter(
            TicketStatus.is_final == True,
            TicketStatus.is_active == True
        ).order_by(TicketStatus.sort_order).all()
    
    def get_customer_visible_statuses(self) -> List[TicketStatus]:
        """Get all customer-visible ticket statuses."""
        return self.db.query(TicketStatus).filter(
            TicketStatus.is_customer_visible == True,
            TicketStatus.is_active == True
        ).order_by(TicketStatus.sort_order).all()
    
    def is_final_status(self, status_id: int) -> bool:
        """Check if ticket status is final."""
        status = self.get_ticket_status(status_id)
        return status.is_final
    
    def pauses_sla(self, status_id: int) -> bool:
        """Check if ticket status pauses SLA timers."""
        status = self.get_ticket_status(status_id)
        return status.pauses_sla
    
    def requires_assignment(self, status_id: int) -> bool:
        """Check if ticket status requires assignment."""
        status = self.get_ticket_status(status_id)
        return status.requires_assignment
    
    def get_escalation_hours(self, status_id: int) -> Optional[int]:
        """Get escalation hours for ticket status."""
        status = self.get_ticket_status(status_id)
        return status.escalation_hours
