"""
Ticket Status History Models
Track all ticket status changes for audit and reporting
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TicketStatusHistory(Base):
    """Track all ticket status changes"""
    __tablename__ = "ticket_status_history"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    
    # Status Change
    previous_status = Column(String(50))  # Using String instead of Enum to avoid circular imports
    new_status = Column(String(50), nullable=False)
    previous_assigned_to = Column(Integer, ForeignKey("administrators.id"))
    new_assigned_to = Column(Integer, ForeignKey("administrators.id"))
    
    # Change Details
    change_reason = Column(String(255))
    change_description = Column(Text)
    
    # Changed By
    changed_by = Column(Integer, ForeignKey("administrators.id"))
    change_method = Column(String(50))                    # manual, automatic, api
    
    # Timestamps
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="status_history")
    changed_by_admin = relationship("Administrator", foreign_keys=[changed_by])
    previous_assignee = relationship("Administrator", foreign_keys=[previous_assigned_to])
    new_assignee = relationship("Administrator", foreign_keys=[new_assigned_to])
