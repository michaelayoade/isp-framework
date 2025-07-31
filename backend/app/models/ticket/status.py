from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.models.foundation.base import Base


class TicketStatus(Base):
    """Ticket status lookup table for admin-configurable support workflow statuses"""

    __tablename__ = "ticket_statuses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String(50), unique=True, nullable=False, index=True
    )  # open, in_progress, resolved, etc.
    name = Column(String(100), nullable=False)  # Display name
    description = Column(String(255))  # Optional description
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System statuses cannot be deleted
    sort_order = Column(Integer, default=0)  # For ordering in UI

    # Workflow properties
    is_initial = Column(
        Boolean, default=False
    )  # Is this a starting status for new tickets
    is_final = Column(
        Boolean, default=False
    )  # Is this a final status (resolved, closed, cancelled)
    requires_assignment = Column(
        Boolean, default=False
    )  # Must ticket be assigned to proceed
    auto_close_after_days = Column(
        Integer
    )  # Auto-close after N days (for resolved tickets)

    # Customer visibility
    is_customer_visible = Column(
        Boolean, default=True
    )  # Should customers see this status
    customer_description = Column(String(255))  # Customer-friendly description

    # SLA properties
    pauses_sla = Column(Boolean, default=False)  # Does this status pause SLA timers
    escalation_hours = Column(Integer)  # Hours before escalation (if applicable)

    # UI properties
    color_hex = Column(
        String(7), default="#6B7280"
    )  # Color for status badges (#RRGGBB)
    icon_name = Column(String(50))  # Icon identifier for UI

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tickets = relationship("Ticket", back_populates="status_ref")
