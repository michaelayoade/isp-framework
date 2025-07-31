"""
Core Ticket Models
Main ticket entity and related models for ISP customer support
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, ForeignKey, ARRAY, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime


class TicketType(enum.Enum):
    SUPPORT = "support"                    # General customer support
    TECHNICAL = "technical"                # Technical issues & troubleshooting
    INCIDENT = "incident"                  # Network incidents/outages
    MAINTENANCE = "maintenance"            # Planned maintenance
    FIELD_WORK = "field_work"             # Field technician work orders
    ABUSE = "abuse"                       # Network abuse reports
    COMPLAINT = "complaint"               # Customer complaints
    COMPLIMENT = "compliment"             # Customer compliments


class TicketPriority(enum.Enum):
    LOW = "low"
    NORMAL = "normal" 
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TicketStatus(enum.Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    PENDING_VENDOR = "pending_vendor"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketSource(enum.Enum):
    CUSTOMER_PORTAL = "customer_portal"
    PHONE = "phone"
    EMAIL = "email"
    CHAT = "chat"
    WALK_IN = "walk_in"
    SYSTEM_AUTOMATED = "system_automated"
    MONITORING = "monitoring"
    STAFF = "staff"
    API = "api"


class Ticket(Base):
    """Core support ticket entity for comprehensive ISP customer support"""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Ticket Classification
    ticket_type = Column(Enum(TicketType), nullable=False, index=True)
    category = Column(String(100), index=True)          # Internet, Voice, General, etc.
    subcategory = Column(String(100))                   # Connection Issue, Slow Speed, etc.
    
    # Customer Context
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    service_id = Column(Integer, ForeignKey("customer_services.id"))
    contact_id = Column(Integer, ForeignKey("customer_contacts.id"))
    
    # Ticket Content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    initial_diagnosis = Column(Text)
    resolution_summary = Column(Text)
    
    # Priority & SLA
    priority = Column(Enum(TicketPriority), default=TicketPriority.NORMAL, index=True)
    urgency = Column(Integer, default=3)                # 1-5 scale
    impact = Column(Integer, default=3)                 # 1-5 scale
    
    # Status Management
    status = Column(Enum(TicketStatus), default=TicketStatus.NEW, index=True)
    substatus = Column(String(100))                     # Additional status details
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey("administrators.id"), index=True)
    assigned_team = Column(String(100))                 # support, technical, field
    assigned_at = Column(DateTime(timezone=True))
    
    # Source & Channel
    source = Column(Enum(TicketSource), nullable=False, index=True)
    source_reference = Column(String(255))              # Email ID, call ID, etc.
    
    # SLA Tracking
    sla_policy_id = Column(Integer, ForeignKey("sla_policies.id"))
    due_date = Column(DateTime(timezone=True), index=True)
    first_response_due = Column(DateTime(timezone=True))
    resolution_due = Column(DateTime(timezone=True))
    
    # Response Tracking
    first_response_at = Column(DateTime(timezone=True))
    first_response_sla_met = Column(Boolean)
    resolution_sla_met = Column(Boolean)
    
    # Location Context (for field work)
    work_location = Column(Text)
    gps_latitude = Column(String(20))
    gps_longitude = Column(String(20))
    location_verified = Column(Boolean, default=False)
    
    # Technical Context
    affected_services = Column(JSONB, default=[])       # List of affected service IDs
    network_devices = Column(JSONB, default=[])         # Affected network devices
    error_codes = Column(JSONB, default=[])             # System error codes
    symptoms = Column(JSONB, default=[])                # Customer-reported symptoms
    
    # Related Records
    related_incident_id = Column(Integer, ForeignKey("network_incidents.id"))
    parent_ticket_id = Column(Integer, ForeignKey("tickets.id"))
    
    # Customer Information
    customer_satisfaction = Column(Integer)              # 1-5 rating
    customer_feedback = Column(Text)
    
    # Time Tracking
    estimated_hours = Column(DECIMAL(5, 2))
    actual_hours = Column(DECIMAL(5, 2))
    
    # Automation & Integration
    auto_created = Column(Boolean, default=False)
    monitoring_alert_id = Column(String(255))
    external_ticket_reference = Column(String(255))
    
    # Tags & Keywords
    tags = Column(ARRAY(String), default=[])
    keywords = Column(ARRAY(String), default=[])        # For search optimization
    
    # Framework Integration
    custom_fields = Column(JSONB, default={})           # Dynamic custom fields
    ticket_rules = Column(JSONB, default={})            # Applied business rules
    workflow_state = Column(JSONB, default={})          # Current workflow state
    automation_history = Column(JSONB, default=[])      # Automation event history
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # Relationships
    customer = relationship("Customer", back_populates="tickets")
    service = relationship("CustomerService")
    contact = relationship("CustomerContact")
    assigned_agent = relationship("Administrator", foreign_keys=[assigned_to])
    sla_policy = relationship("SLAPolicy", back_populates="tickets")
    
    # Ticket interactions
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    file_attachments = relationship("FileMetadata", back_populates="ticket", cascade="all, delete-orphan")
    status_history = relationship("TicketStatusHistory", back_populates="ticket", cascade="all, delete-orphan")
    escalations = relationship("TicketEscalation", back_populates="ticket", cascade="all, delete-orphan")
    time_entries = relationship("TicketTimeEntry", back_populates="ticket", cascade="all, delete-orphan")
    
    # Field work
    field_work = relationship("FieldWorkOrder", back_populates="ticket", uselist=False)
    
    # Related tickets
    parent_ticket = relationship("Ticket", remote_side=[id])
    child_tickets = relationship("Ticket", back_populates="parent_ticket")

    def __repr__(self):
        return f"<Ticket {self.ticket_number}: {self.title} [{self.status.value}]>"

    @property
    def is_overdue(self):
        """Check if ticket is overdue"""
        if not self.due_date:
            return False
        return datetime.now(self.due_date.tzinfo) > self.due_date

    @property
    def sla_time_remaining_hours(self):
        """Calculate SLA time remaining in hours"""
        if not self.due_date:
            return None
        
        now = datetime.now(self.due_date.tzinfo)
        if now >= self.due_date:
            return 0
        
        delta = self.due_date - now
        return round(delta.total_seconds() / 3600, 2)

    @property
    def response_time_hours(self):
        """Calculate actual response time"""
        if not self.first_response_at:
            return None
        
        delta = self.first_response_at - self.created_at
        return round(delta.total_seconds() / 3600, 2)

    @property
    def resolution_time_hours(self):
        """Calculate total resolution time"""
        if not self.resolved_at:
            return None
        
        delta = self.resolved_at - self.created_at
        return round(delta.total_seconds() / 3600, 2)

    def add_automation_event(self, event_type, description, triggered_by=None):
        """Add automation event to history"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'description': description,
            'triggered_by': triggered_by
        }
        
        if not self.automation_history:
            self.automation_history = []
        
        self.automation_history = self.automation_history + [event]


class TicketMessage(Base):
    """Messages and communications within tickets"""
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    
    # Message Content
    message_type = Column(String(50), default='comment')  # comment, solution, note, email, sms
    subject = Column(String(255))
    content = Column(Text, nullable=False)
    content_format = Column(String(20), default='text')   # text, html, markdown
    
    # Author Information
    author_type = Column(String(50), nullable=False)      # customer, agent, system
    author_id = Column(Integer)                           # Customer or Admin ID
    author_name = Column(String(255))
    author_email = Column(String(255))
    
    # Message Properties
    is_internal = Column(Boolean, default=False)          # Internal notes vs customer-visible
    is_solution = Column(Boolean, default=False)          # Marked as solution
    is_auto_generated = Column(Boolean, default=False)
    
    # Communication Tracking
    email_sent = Column(Boolean, default=False)
    sms_sent = Column(Boolean, default=False)
    push_notification_sent = Column(Boolean, default=False)
    
    # External Integration
    email_message_id = Column(String(255))                # Email system message ID
    external_reference = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ticket = relationship("Ticket", back_populates="messages")
    attachments = relationship("MessageAttachment", back_populates="message", cascade="all, delete-orphan")


class TicketAttachment(Base):
    """File attachments for tickets"""
    __tablename__ = "ticket_attachments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("ticket_messages.id"))
    
    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    file_hash = Column(String(64))
    
    # Attachment Type
    attachment_type = Column(String(50), default='document')  # document, image, video, log
    description = Column(String(500))
    
    # Access Control
    is_public = Column(Boolean, default=False)            # Visible to customer
    requires_authentication = Column(Boolean, default=True)
    
    # Uploaded By
    uploaded_by = Column(Integer, ForeignKey("administrators.id"))
    uploaded_by_customer = Column(Integer, ForeignKey("customers.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("Ticket", back_populates="attachments")
    uploader = relationship("Administrator")
    customer_uploader = relationship("Customer")


class MessageAttachment(Base):
    """Attachments specific to ticket messages"""
    __tablename__ = "message_attachments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("ticket_messages.id", ondelete="CASCADE"), nullable=False)
    
    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("TicketMessage", back_populates="attachments")
