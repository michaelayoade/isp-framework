"""
Ticket Escalation Models
Escalation management for customer support tickets
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class EscalationReason(enum.Enum):
    SLA_BREACH = "sla_breach"
    CUSTOMER_REQUEST = "customer_request"
    COMPLEXITY = "complexity"
    MANAGER_DECISION = "manager_decision"
    REPEATED_ISSUE = "repeated_issue"


class TicketEscalation(Base):
    """Ticket escalation records"""

    __tablename__ = "ticket_escalations"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(
        Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )

    # Escalation Details
    escalation_reason = Column(Enum(EscalationReason), nullable=False)
    escalation_level = Column(Integer, default=1)  # 1st level, 2nd level, etc.

    # From/To
    escalated_from = Column(Integer, ForeignKey("administrators.id"))
    escalated_to = Column(Integer, ForeignKey("administrators.id"))
    escalated_from_team = Column(String(100))
    escalated_to_team = Column(String(100))

    # Escalation Content
    escalation_notes = Column(Text)
    urgency_justification = Column(Text)

    # Response
    response_notes = Column(Text)
    response_action = Column(String(100))  # accepted, rejected, reassigned
    responded_at = Column(DateTime(timezone=True))
    responded_by = Column(Integer, ForeignKey("administrators.id"))

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    escalated_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    ticket = relationship("Ticket", back_populates="escalations")
    escalator = relationship("Administrator", foreign_keys=[escalated_from])
    escalatee = relationship("Administrator", foreign_keys=[escalated_to])
    responder = relationship("Administrator", foreign_keys=[responded_by])
