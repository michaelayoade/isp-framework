"""
Ticket Time Tracking Models
Time tracking for ticket work and billing
"""

from sqlalchemy import DECIMAL, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class TicketTimeEntry(Base):
    """Time tracking for ticket work"""

    __tablename__ = "ticket_time_entries"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(
        Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )

    # Time Details
    hours_worked = Column(DECIMAL(5, 2), nullable=False)
    work_description = Column(Text, nullable=False)
    work_type = Column(String(50))  # research, diagnosis, resolution, communication

    # Work Period
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))

    # Worker
    worked_by = Column(Integer, ForeignKey("administrators.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="time_entries")
    worker = relationship("Administrator")
