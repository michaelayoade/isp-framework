"""
Ticketing System Models
Comprehensive customer support ticket management for ISP Framework
"""

from .escalation import EscalationReason, TicketEscalation
from .field_work import FieldWorkOrder, FieldWorkStatus
from .incidents import NetworkIncident
from .knowledge_base import KnowledgeBaseArticle
from .sla import SLAPolicy
from .status_history import TicketStatusHistory
from .templates import TicketTemplate
from .tickets import (
    MessageAttachment,
    Ticket,
    TicketAttachment,
    TicketMessage,
    TicketPriority,
    TicketSource,
    TicketStatus,
    TicketType,
)
from .time_tracking import TicketTimeEntry

__all__ = [
    # Core ticket models
    "Ticket",
    "TicketType",
    "TicketPriority",
    "TicketStatus",
    "TicketSource",
    "TicketMessage",
    "TicketAttachment",
    "MessageAttachment",
    # SLA and escalation
    "SLAPolicy",
    "TicketEscalation",
    "EscalationReason",
    "TicketStatusHistory",
    # Time tracking and field work
    "TicketTimeEntry",
    "FieldWorkOrder",
    "FieldWorkStatus",
    # Incidents and knowledge base
    "NetworkIncident",
    "KnowledgeBaseArticle",
    "TicketTemplate",
]
