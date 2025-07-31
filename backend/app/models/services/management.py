"""
ISP Service Management System - Service Management

Service management models for IP assignment, status tracking, and suspension management.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, DECIMAL, Enum
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.services.enums import (
    ServiceStatus, IPAssignmentType, SuspensionReason, SuspensionType, ChangeMethod
)
from datetime import datetime


class ServiceIPAssignment(Base):
    """IP address assignments for customer services"""
    __tablename__ = "service_ip_assignments"

    id = Column(Integer, primary_key=True, index=True)
    customer_service_id = Column(Integer, ForeignKey("customer_services.id", ondelete="CASCADE"), nullable=False)
    
    # IP Configuration
    ip_address = Column(INET, nullable=False, index=True)
    subnet_mask = Column(INET)
    gateway = Column(INET)
    
    # DNS Configuration
    dns_primary = Column(INET)
    dns_secondary = Column(INET)
    dns_servers = Column(JSONB, default=list)
    
    # Assignment Type
    assignment_type = Column(Enum(IPAssignmentType), nullable=False)
    ip_pool_id = Column(Integer, ForeignKey("ip_pools.id"))
    
    # DHCP Configuration (if applicable)
    dhcp_lease_time = Column(Integer)  # seconds
    dhcp_options = Column(JSONB, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    assignment_date = Column(DateTime(timezone=True), server_default=func.now())
    release_date = Column(DateTime(timezone=True))
    
    # Usage Tracking
    last_seen_online = Column(DateTime(timezone=True))
    total_sessions = Column(Integer, default=0)
    total_bytes_in = Column(DECIMAL(15, 0), default=0)
    total_bytes_out = Column(DECIMAL(15, 0), default=0)
    
    # Network Information
    mac_address = Column(String(17))  # MAC address if known
    hostname = Column(String(255))    # Device hostname if available
    user_agent = Column(Text)         # Browser user agent if captured
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer_service = relationship("CustomerService", back_populates="ip_assignments")
    ip_pool = relationship("IPPool", foreign_keys=[ip_pool_id])
    
    def __repr__(self):
        return f"<ServiceIPAssignment {self.ip_address}: {self.assignment_type.value}>"

    @property
    def is_currently_assigned(self):
        """Check if IP is currently assigned and active"""
        return self.is_active and not self.release_date

    @property
    def assignment_duration_days(self):
        """Calculate how long IP has been assigned"""
        if not self.assignment_date:
            return 0
        
        end_date = self.release_date or datetime.now(self.assignment_date.tzinfo)
        return (end_date - self.assignment_date).days

    @property
    def total_traffic_gb(self):
        """Calculate total traffic in GB"""
        total_bytes = float(self.total_bytes_in or 0) + float(self.total_bytes_out or 0)
        return round(total_bytes / (1024**3), 2)


class ServiceStatusHistory(Base):
    """Track all service status changes"""
    __tablename__ = "service_status_history"

    id = Column(Integer, primary_key=True, index=True)
    customer_service_id = Column(Integer, ForeignKey("customer_services.id", ondelete="CASCADE"), nullable=False)
    
    # Status Change
    previous_status = Column(Enum(ServiceStatus))
    new_status = Column(Enum(ServiceStatus), nullable=False)
    change_reason = Column(String(255))
    change_description = Column(Text)
    
    # Change Context
    changed_by = Column(Integer, ForeignKey("administrators.id"))
    change_method = Column(Enum(ChangeMethod), default=ChangeMethod.MANUAL)
    related_ticket_id = Column(Integer)  # ForeignKey("tickets.id") - commented until tickets table exists
    related_invoice_id = Column(Integer, ForeignKey("invoices.id"))
    
    # Additional Information
    system_notes = Column(Text)
    customer_impact = Column(String(100))  # none, low, medium, high, critical
    downtime_minutes = Column(Integer, default=0)
    
    # Automation Information
    automated_change = Column(Boolean, default=False)
    automation_rule_id = Column(Integer)
    automation_trigger = Column(String(100))
    
    # Timestamps
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    effective_at = Column(DateTime(timezone=True))  # When change actually took effect
    
    # Relationships
    customer_service = relationship("CustomerService", back_populates="status_history")
    changed_by_admin = relationship("Administrator")

    def __repr__(self):
        return f"<ServiceStatusHistory {self.customer_service_id}: {self.previous_status} -> {self.new_status}>"

    @property
    def status_change_display(self):
        """Human-readable status change"""
        prev = self.previous_status.value if self.previous_status else "None"
        return f"{prev} → {self.new_status.value}"

    @property
    def change_age_hours(self):
        """Calculate hours since status change"""
        now = datetime.now(self.changed_at.tzinfo)
        return round((now - self.changed_at).total_seconds() / 3600, 1)


class ServiceSuspension(Base):
    """Service suspension records with detailed tracking"""
    __tablename__ = "service_suspensions"

    id = Column(Integer, primary_key=True, index=True)
    customer_service_id = Column(Integer, ForeignKey("customer_services.id", ondelete="CASCADE"), nullable=False)
    
    # Suspension Details
    suspension_reason = Column(Enum(SuspensionReason), nullable=False, index=True)
    suspension_date = Column(DateTime(timezone=True), nullable=False, index=True)
    scheduled_restoration_date = Column(DateTime(timezone=True))
    
    # Suspension Configuration
    suspension_type = Column(Enum(SuspensionType), default=SuspensionType.FULL)
    reduced_speed_kbps = Column(Integer)  # For speed-limited suspensions
    
    # Billing Integration
    related_invoice_id = Column(Integer, ForeignKey("invoices.id"))
    overdue_amount = Column(DECIMAL(12, 2))
    minimum_payment_amount = Column(DECIMAL(12, 2))
    
    # Restoration
    restoration_date = Column(DateTime(timezone=True))
    restored_by = Column(Integer, ForeignKey("administrators.id"))
    restoration_payment_id = Column(Integer, ForeignKey("payments.id"))
    restoration_notes = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Automation
    auto_restore_conditions = Column(JSONB, default=dict)  # Conditions for auto-restoration
    auto_suspend_conditions = Column(JSONB, default=dict)  # Conditions that triggered suspension
    
    # Customer Communication
    customer_notified = Column(Boolean, default=False)
    notification_method = Column(String(50))  # email, sms, call, portal
    notification_sent_at = Column(DateTime(timezone=True))
    
    # Grace Period
    grace_period_hours = Column(Integer, default=0)
    grace_period_expires = Column(DateTime(timezone=True))
    grace_period_used = Column(Boolean, default=False)
    
    # Escalation
    escalation_level = Column(Integer, default=1)  # 1-5
    next_escalation_date = Column(DateTime(timezone=True))
    final_notice_sent = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer_service = relationship("CustomerService", back_populates="suspensions")
    related_invoice = relationship("Invoice")
    restorer = relationship("Administrator")
    restoration_payment = relationship("Payment")

    def __repr__(self):
        return f"<ServiceSuspension {self.customer_service_id}: {self.suspension_reason.value}>"

    @property
    def suspension_duration_days(self):
        """Calculate suspension duration"""
        end_date = self.restoration_date or datetime.now(self.suspension_date.tzinfo)
        return (end_date - self.suspension_date).days

    @property
    def suspension_duration_hours(self):
        """Calculate suspension duration in hours"""
        end_date = self.restoration_date or datetime.now(self.suspension_date.tzinfo)
        return round((end_date - self.suspension_date).total_seconds() / 3600, 1)

    @property
    def is_in_grace_period(self):
        """Check if suspension is still in grace period"""
        if not self.grace_period_expires or self.grace_period_used:
            return False
        
        now = datetime.now(self.grace_period_expires.tzinfo)
        return now < self.grace_period_expires

    @property
    def days_until_restoration(self):
        """Calculate days until scheduled restoration"""
        if not self.scheduled_restoration_date or self.restoration_date:
            return None
        
        now = datetime.now(self.scheduled_restoration_date.tzinfo)
        delta = self.scheduled_restoration_date - now
        return max(0, delta.days)

    @property
    def can_auto_restore(self):
        """Check if suspension can be automatically restored"""
        if not self.is_active or self.restoration_date:
            return False
        
        conditions = self.auto_restore_conditions or {}
        
        # Check payment condition
        if conditions.get('payment_received') and self.related_invoice:
            min_payment_percent = conditions.get('minimum_payment_percent', 100)
            self.overdue_amount * (min_payment_percent / 100)
            
            # This would need to check actual payments against the invoice
            # Implementation would query payment records
            pass
        
        return False


class ServiceUsageTracking(Base):
    """Track service usage patterns and statistics"""
    __tablename__ = "service_usage_tracking"

    id = Column(Integer, primary_key=True, index=True)
    customer_service_id = Column(Integer, ForeignKey("customer_services.id", ondelete="CASCADE"), nullable=False)
    
    # Time Period
    tracking_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly
    
    # Internet Usage (if applicable)
    bytes_downloaded = Column(DECIMAL(15, 0), default=0)
    bytes_uploaded = Column(DECIMAL(15, 0), default=0)
    session_count = Column(Integer, default=0)
    session_duration_minutes = Column(Integer, default=0)
    peak_download_speed_kbps = Column(Integer)
    peak_upload_speed_kbps = Column(Integer)
    average_latency_ms = Column(DECIMAL(6, 2))
    
    # Voice Usage (if applicable)
    incoming_calls = Column(Integer, default=0)
    outgoing_calls = Column(Integer, default=0)
    total_call_minutes = Column(Integer, default=0)
    missed_calls = Column(Integer, default=0)
    voicemail_messages = Column(Integer, default=0)
    
    # Quality Metrics
    uptime_minutes = Column(Integer, default=0)
    downtime_minutes = Column(Integer, default=0)
    packet_loss_percent = Column(DECIMAL(5, 2))
    jitter_ms = Column(DECIMAL(6, 2))
    
    # Cost Information
    usage_charges = Column(DECIMAL(10, 2), default=0)
    overage_charges = Column(DECIMAL(10, 2), default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer_service = relationship("CustomerService")

    def __repr__(self):
        return f"<ServiceUsageTracking {self.customer_service_id}: {self.tracking_date}>"

    @property
    def total_traffic_gb(self):
        """Calculate total traffic in GB"""
        total_bytes = float(self.bytes_downloaded or 0) + float(self.bytes_uploaded or 0)
        return round(total_bytes / (1024**3), 2)

    @property
    def uptime_percent(self):
        """Calculate uptime percentage"""
        total_minutes = self.uptime_minutes + self.downtime_minutes
        if total_minutes == 0:
            return 100.0
        
        return round((self.uptime_minutes / total_minutes) * 100, 2)

    @property
    def average_session_duration_minutes(self):
        """Calculate average session duration"""
        if self.session_count == 0:
            return 0
        
        return round(self.session_duration_minutes / self.session_count, 1)


class ServiceAlert(Base):
    """Service alerts and notifications"""
    __tablename__ = "service_alerts"

    id = Column(Integer, primary_key=True, index=True)
    customer_service_id = Column(Integer, ForeignKey("customer_services.id", ondelete="CASCADE"), nullable=False)
    
    # Alert Information
    alert_type = Column(String(50), nullable=False, index=True)  # usage, performance, billing, etc.
    severity = Column(String(20), default='medium')  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert Conditions
    trigger_condition = Column(JSONB)  # Condition that triggered alert
    threshold_value = Column(String(100))
    current_value = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("administrators.id"))
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("administrators.id"))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Automation
    auto_generated = Column(Boolean, default=False)
    alert_rule_id = Column(Integer)
    
    # Customer Notification
    customer_notified = Column(Boolean, default=False)
    customer_notification_sent_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer_service = relationship("CustomerService")
    acknowledger = relationship("Administrator", foreign_keys=[acknowledged_by])
    resolver = relationship("Administrator", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<ServiceAlert {self.customer_service_id}: {self.alert_type} - {self.severity}>"

    @property
    def alert_age_hours(self):
        """Calculate alert age in hours"""
        now = datetime.now(self.created_at.tzinfo)
        return round((now - self.created_at).total_seconds() / 3600, 1)

    @property
    def resolution_time_hours(self):
        """Calculate time to resolution"""
        if not self.resolved_at:
            return None
        
        return round((self.resolved_at - self.created_at).total_seconds() / 3600, 1)


# Performance indexes
# Index already imported at the top of the file

# IP assignment indexes
Index('idx_ip_assignments_ip', ServiceIPAssignment.ip_address)
Index('idx_ip_assignments_active', ServiceIPAssignment.is_active)
Index('idx_ip_assignments_service', ServiceIPAssignment.customer_service_id)

# Status history indexes
Index('idx_status_history_service_date', ServiceStatusHistory.customer_service_id, ServiceStatusHistory.changed_at)
Index('idx_status_history_status', ServiceStatusHistory.new_status, ServiceStatusHistory.changed_at)

# Suspension indexes
Index('idx_suspensions_active', ServiceSuspension.is_active, ServiceSuspension.suspension_date)
Index('idx_suspensions_reason', ServiceSuspension.suspension_reason)
Index('idx_suspensions_restoration', ServiceSuspension.scheduled_restoration_date)

# Usage tracking indexes
Index('idx_usage_tracking_service_date', ServiceUsageTracking.customer_service_id, ServiceUsageTracking.tracking_date)
Index('idx_usage_tracking_period', ServiceUsageTracking.period_type, ServiceUsageTracking.tracking_date)

# Alert indexes
Index('idx_alerts_active', ServiceAlert.is_active, ServiceAlert.severity)
Index('idx_alerts_type', ServiceAlert.alert_type, ServiceAlert.created_at)
Index('idx_alerts_service', ServiceAlert.customer_service_id, ServiceAlert.is_active)
