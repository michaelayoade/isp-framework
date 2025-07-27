"""
Ticketing System Models
Comprehensive customer support ticket management for ISP Framework
"""

from .tickets import (
    Ticket, TicketType, TicketPriority, TicketStatus, TicketSource,
    TicketMessage, TicketAttachment, MessageAttachment
)
from .sla import SLAPolicy
from .escalation import TicketEscalation, EscalationReason
from .status_history import TicketStatusHistory
from .time_tracking import TicketTimeEntry
from .field_work import FieldWorkOrder, FieldWorkStatus
from .incidents import NetworkIncident
from .knowledge_base import KnowledgeBaseArticle
from .templates import TicketTemplate

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
    "TicketTemplate"
]
