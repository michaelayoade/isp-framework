"""
Ticket Template Models
Templates for common ticket types and automation
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TicketTemplate(Base):
    """Templates for common ticket types"""
    __tablename__ = "ticket_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Template Configuration
    ticket_type = Column(String(50), nullable=False)  # Using String to avoid circular imports
    category = Column(String(100))
    subcategory = Column(String(100))
    priority = Column(String(20), default='normal')
    
    # Content Templates
    title_template = Column(String(255))
    description_template = Column(Text)
    
    # Assignment Rules
    auto_assign_team = Column(String(100))
    auto_assign_agent = Column(Integer, ForeignKey("administrators.id"))
    
    # SLA
    sla_policy_id = Column(Integer, ForeignKey("sla_policies.id"))
    
    # Workflow (Framework Integration)
    require_customer_info = Column(Boolean, default=True)
    require_service_info = Column(Boolean, default=False)
    require_location_info = Column(Boolean, default=False)
    custom_fields_required = Column(JSONB, default=[])
    default_custom_fields = Column(JSONB, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)             # Available to customers
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    auto_assignee = relationship("Administrator")
    sla_policy = relationship("SLAPolicy")
