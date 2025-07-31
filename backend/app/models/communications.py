"""
Communications Models for ISP Framework

Handles email, SMS, and notification management with template support,
delivery tracking, and plugin-ready architecture for future extensions.
"""

from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
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


class CommunicationType(PyEnum):
    """Types of communications"""

    EMAIL = "email"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    WEBHOOK = "webhook"
    VOICE_CALL = "voice_call"


class CommunicationStatus(PyEnum):
    """Communication delivery status"""

    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class CommunicationPriority(PyEnum):
    """Communication priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TemplateCategory(PyEnum):
    """Template categories for organization"""

    CUSTOMER_ONBOARDING = "customer_onboarding"
    BILLING = "billing"
    SERVICE_ALERTS = "service_alerts"
    SUPPORT = "support"
    MARKETING = "marketing"
    SYSTEM = "system"
    AUTHENTICATION = "authentication"
    NETWORK = "network"


class CommunicationTemplate(Base):
    """Jinja2 templates for dynamic content generation"""

    __tablename__ = "communication_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(Enum(TemplateCategory), nullable=False)
    communication_type = Column(Enum(CommunicationType), nullable=False)

    # Template content
    subject_template = Column(Text)  # For emails
    body_template = Column(Text, nullable=False)  # Main content
    html_template = Column(Text)  # HTML version for emails

    # Configuration
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System templates can't be deleted
    language = Column(String(10), default="en")

    # Template variables documentation
    required_variables = Column(JSON, default=list)  # List of required template vars
    optional_variables = Column(JSON, default=list)  # List of optional template vars
    sample_data = Column(JSON, default=dict)  # Sample data for testing

    # Metadata
    description = Column(Text)
    version = Column(String(20), default="1.0")
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("Administrator")
    communications = relationship("CommunicationLog", back_populates="template")


class CommunicationProvider(Base):
    """Communication service providers (SMTP, SMS gateways, etc.)"""

    __tablename__ = "communication_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    provider_type = Column(Enum(CommunicationType), nullable=False)

    # Provider configuration
    provider_class = Column(String(255), nullable=False)  # Python class for provider
    configuration = Column(JSON, default=dict)  # Provider-specific config
    credentials = Column(JSON, default=dict)  # Encrypted credentials

    # Settings
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    priority = Column(Integer, default=100)  # Lower = higher priority

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    rate_limit_per_day = Column(Integer, default=10000)

    # Monitoring
    success_rate = Column(Integer, default=100)  # Percentage
    average_delivery_time = Column(Integer, default=0)  # Seconds
    last_used = Column(DateTime(timezone=True))

    # Metadata
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    communications = relationship("CommunicationLog", back_populates="provider")


class CommunicationLog(Base):
    """Log of all communications sent through the system"""

    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Communication details
    communication_type = Column(Enum(CommunicationType), nullable=False)
    status = Column(Enum(CommunicationStatus), default=CommunicationStatus.PENDING)
    priority = Column(Enum(CommunicationPriority), default=CommunicationPriority.NORMAL)

    # Recipients
    recipient_email = Column(String(255))
    recipient_phone = Column(String(50))
    recipient_name = Column(String(255))

    # Content
    subject = Column(String(500))
    body = Column(Text, nullable=False)
    html_body = Column(Text)

    # Relationships
    template_id = Column(
        Integer, ForeignKey("communication_templates.id"), nullable=True
    )
    provider_id = Column(
        Integer, ForeignKey("communication_providers.id"), nullable=True
    )
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=True)

    # Context
    context_type = Column(String(50))  # billing, support, service, etc.
    context_id = Column(Integer)  # ID of related object (invoice, ticket, etc.)
    template_variables = Column(JSON, default=dict)  # Variables used in template

    # Delivery tracking
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))  # For emails
    clicked_at = Column(DateTime(timezone=True))  # For emails with links

    # Provider response
    provider_message_id = Column(String(255))  # External provider's message ID
    provider_response = Column(JSON, default=dict)  # Full provider response
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    template = relationship("CommunicationTemplate", back_populates="communications")
    provider = relationship("CommunicationProvider", back_populates="communications")
    customer = relationship("Customer", back_populates="communications")
    admin = relationship("Administrator")


class CommunicationQueue(Base):
    """Queue for batch processing of communications"""

    __tablename__ = "communication_queue"

    id = Column(Integer, primary_key=True, index=True)

    # Queue details
    queue_name = Column(String(255), nullable=False)
    communication_type = Column(Enum(CommunicationType), nullable=False)
    priority = Column(Enum(CommunicationPriority), default=CommunicationPriority.NORMAL)

    # Batch information
    total_recipients = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # Template and content
    template_id = Column(
        Integer, ForeignKey("communication_templates.id"), nullable=True
    )
    subject = Column(String(500))
    body = Column(Text)
    html_body = Column(Text)

    # Recipients (JSON array of recipient objects)
    recipients = Column(JSON, default=list)
    template_variables = Column(
        JSON, default=dict
    )  # Global variables for all recipients

    # Processing
    status = Column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    scheduled_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Configuration
    provider_id = Column(
        Integer, ForeignKey("communication_providers.id"), nullable=True
    )
    batch_size = Column(Integer, default=100)  # Process in batches
    delay_between_batches = Column(Integer, default=60)  # Seconds

    # Metadata
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    template = relationship("CommunicationTemplate")
    provider = relationship("CommunicationProvider")
    creator = relationship("Administrator")


class CommunicationPreference(Base):
    """Customer communication preferences"""

    __tablename__ = "communication_preferences"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Email preferences
    email_enabled = Column(Boolean, default=True)
    email_billing = Column(Boolean, default=True)
    email_service_alerts = Column(Boolean, default=True)
    email_support = Column(Boolean, default=True)
    email_marketing = Column(Boolean, default=False)
    email_system = Column(Boolean, default=True)

    # SMS preferences
    sms_enabled = Column(Boolean, default=True)
    sms_billing = Column(Boolean, default=False)
    sms_service_alerts = Column(Boolean, default=True)
    sms_support = Column(Boolean, default=False)
    sms_marketing = Column(Boolean, default=False)
    sms_system = Column(Boolean, default=True)

    # Push notification preferences
    push_enabled = Column(Boolean, default=True)
    push_billing = Column(Boolean, default=True)
    push_service_alerts = Column(Boolean, default=True)
    push_support = Column(Boolean, default=True)
    push_marketing = Column(Boolean, default=False)
    push_system = Column(Boolean, default=True)

    # Timing preferences
    quiet_hours_start = Column(String(5), default="22:00")  # HH:MM format
    quiet_hours_end = Column(String(5), default="08:00")
    timezone = Column(String(50), default="UTC")

    # Language preference
    preferred_language = Column(String(10), default="en")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="communication_preferences")


class CommunicationRule(Base):
    """Automated communication rules and triggers"""

    __tablename__ = "communication_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Trigger configuration
    trigger_event = Column(
        String(100), nullable=False
    )  # customer.created, invoice.overdue, etc.
    trigger_conditions = Column(JSON, default=dict)  # Conditions to check

    # Communication settings
    template_id = Column(
        Integer, ForeignKey("communication_templates.id"), nullable=False
    )
    communication_type = Column(Enum(CommunicationType), nullable=False)
    priority = Column(Enum(CommunicationPriority), default=CommunicationPriority.NORMAL)

    # Timing
    delay_minutes = Column(Integer, default=0)  # Delay before sending

    # Status
    is_active = Column(Boolean, default=True)

    # Statistics
    triggered_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # Metadata
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    template = relationship("CommunicationTemplate")
    creator = relationship("Administrator")


# Add relationships to existing models
# These will be added via migration scripts or model updates

"""
# Add to Customer model:
communications = relationship("CommunicationLog", back_populates="customer")
communication_preferences = relationship("CommunicationPreference", back_populates="customer", uselist=False)
"""
