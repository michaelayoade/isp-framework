"""
SLA Policy Models
Service Level Agreement management for ticket support
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ARRAY, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class SLAPolicy(Base):
    """Service Level Agreement policies for different ticket types"""
    __tablename__ = "sla_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Applicability
    ticket_types = Column(ARRAY(String), default=[])      # Which ticket types this applies to
    customer_types = Column(ARRAY(String), default=[])    # residential, business, enterprise
    
    # Response Time SLA (in minutes)
    first_response_time = Column(Integer, nullable=False)
    
    # Resolution Time SLA by Priority (in minutes)
    critical_resolution_time = Column(Integer, nullable=False)
    urgent_resolution_time = Column(Integer, nullable=False)
    high_resolution_time = Column(Integer, nullable=False)
    normal_resolution_time = Column(Integer, nullable=False)
    low_resolution_time = Column(Integer, nullable=False)
    
    # Escalation Rules
    auto_escalate_enabled = Column(Boolean, default=True)
    escalation_threshold_percent = Column(Integer, default=80)  # Escalate at 80% of SLA time
    
    # Business Hours
    business_hours_only = Column(Boolean, default=False)
    business_hours_start = Column(String(10), default='09:00')   # HH:MM format
    business_hours_end = Column(String(10), default='17:00')
    business_days = Column(ARRAY(Integer), default=[1,2,3,4,5])  # Monday=1, Sunday=7
    timezone = Column(String(50), default='UTC')
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tickets = relationship("Ticket", back_populates="sla_policy")

    def get_resolution_time_for_priority(self, priority):
        """Get resolution time based on priority"""
        from .tickets import TicketPriority
        
        if priority == TicketPriority.CRITICAL:
            return self.critical_resolution_time
        elif priority == TicketPriority.URGENT:
            return self.urgent_resolution_time
        elif priority == TicketPriority.HIGH:
            return self.high_resolution_time
        elif priority == TicketPriority.NORMAL:
            return self.normal_resolution_time
        else:  # LOW
            return self.low_resolution_time
