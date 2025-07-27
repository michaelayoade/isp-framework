"""
Billing Cycles Management

Automated billing cycle processing with flexible scheduling,
batch invoice generation, and comprehensive cycle tracking.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone, timedelta
from ..base import Base
from .enums import BillingCycleType


class BillingCycle(Base):
    """Billing cycle management"""
    __tablename__ = "billing_cycles"

    id = Column(Integer, primary_key=True, index=True)
    cycle_name = Column(String(100), nullable=False)
    cycle_type = Column(SQLEnum(BillingCycleType), nullable=False)
    
    # Cycle configuration
    cycle_day = Column(Integer, nullable=False)  # Day of month/week
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    
    # Processing status
    status = Column(String(20), nullable=False, default="active", index=True)
    invoices_generated = Column(Boolean, default=False)
    generation_date = Column(DateTime(timezone=True))
    
    # Statistics
    total_customers = Column(Integer, default=0)
    total_invoices = Column(Integer, default=0)
    total_amount = Column(DECIMAL(12, 2), default=0)
    
    # Automation
    auto_generate = Column(Boolean, default=True)
    auto_send = Column(Boolean, default=False)
    
    # Processing settings
    batch_size = Column(Integer, default=100)  # Number of invoices per batch
    processing_delay_minutes = Column(Integer, default=0)
    
    # Metadata
    description = Column(Text)
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    invoices = relationship("Invoice", back_populates="billing_cycle")

    def __repr__(self):
        return f"<BillingCycle(id={self.id}, name='{self.cycle_name}', type={self.cycle_type})>"

    @property
    def is_current(self):
        """Check if this is the current billing cycle"""
        now = datetime.now(timezone.utc)
        return self.start_date <= now <= self.end_date

    @property
    def is_ready_for_generation(self):
        """Check if cycle is ready for invoice generation"""
        return (self.status == "active" and 
                not self.invoices_generated and 
                datetime.now(timezone.utc) >= self.start_date)

    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.due_date <= datetime.now(timezone.utc):
            return 0
        return (self.due_date - datetime.now(timezone.utc)).days

    def calculate_next_cycle_dates(self):
        """Calculate dates for the next billing cycle"""
        if self.cycle_type == BillingCycleType.MONTHLY:
            next_start = self.end_date + timedelta(days=1)
            if next_start.month == 12:
                next_end = next_start.replace(year=next_start.year + 1, month=1, day=self.cycle_day) - timedelta(days=1)
            else:
                next_end = next_start.replace(month=next_start.month + 1, day=self.cycle_day) - timedelta(days=1)
        elif self.cycle_type == BillingCycleType.QUARTERLY:
            next_start = self.end_date + timedelta(days=1)
            next_end = next_start + timedelta(days=90)  # Approximate quarter
        elif self.cycle_type == BillingCycleType.ANNUAL:
            next_start = self.end_date + timedelta(days=1)
            next_end = next_start.replace(year=next_start.year + 1) - timedelta(days=1)
        else:
            # Custom cycle - use the same duration
            duration = self.end_date - self.start_date
            next_start = self.end_date + timedelta(days=1)
            next_end = next_start + duration
        
        # Due date is typically 30 days after cycle end
        next_due = next_end + timedelta(days=30)
        
        return next_start, next_end, next_due

    def mark_as_generated(self, invoice_count, total_amount):
        """Mark cycle as having invoices generated"""
        self.invoices_generated = True
        self.generation_date = datetime.now(timezone.utc)
        self.total_invoices = invoice_count
        self.total_amount = total_amount

    def get_cycle_summary(self):
        """Get comprehensive billing cycle summary"""
        return {
            "cycle_name": self.cycle_name,
            "cycle_type": self.cycle_type.value,
            "cycle_day": self.cycle_day,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "status": self.status,
            "invoices_generated": self.invoices_generated,
            "generation_date": self.generation_date.isoformat() if self.generation_date else None,
            "statistics": {
                "total_customers": self.total_customers,
                "total_invoices": self.total_invoices,
                "total_amount": float(self.total_amount)
            },
            "automation": {
                "auto_generate": self.auto_generate,
                "auto_send": self.auto_send,
                "batch_size": self.batch_size,
                "processing_delay_minutes": self.processing_delay_minutes
            },
            "is_current": self.is_current,
            "is_ready_for_generation": self.is_ready_for_generation,
            "days_until_due": self.days_until_due
        }


class BillingCycleCustomer(Base):
    """Customer assignments to billing cycles"""
    __tablename__ = "billing_cycle_customers"

    id = Column(Integer, primary_key=True, index=True)
    billing_cycle_id = Column(Integer, ForeignKey("billing_cycles.id"), nullable=False)
    billing_account_id = Column(Integer, ForeignKey("customer_billing_accounts.id"), nullable=False)
    
    # Assignment details
    assigned_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Processing status
    invoice_generated = Column(Boolean, default=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    generation_date = Column(DateTime(timezone=True))
    
    # Proration settings
    prorate_first_cycle = Column(Boolean, default=True)
    prorate_last_cycle = Column(Boolean, default=True)
    
    # Metadata
    notes = Column(Text)
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    billing_cycle = relationship("BillingCycle")
    billing_account = relationship("CustomerBillingAccount")
    invoice = relationship("Invoice", foreign_keys=[invoice_id])

    def __repr__(self):
        return f"<BillingCycleCustomer(id={self.id}, cycle_id={self.billing_cycle_id}, account_id={self.billing_account_id})>"

    def mark_invoice_generated(self, invoice_id):
        """Mark invoice as generated for this customer"""
        self.invoice_generated = True
        self.invoice_id = invoice_id
        self.generation_date = datetime.now(timezone.utc)


class BillingCycleTemplate(Base):
    """Templates for creating billing cycles"""
    __tablename__ = "billing_cycle_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False, unique=True)
    cycle_type = Column(SQLEnum(BillingCycleType), nullable=False)
    
    # Template configuration
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Cycle settings
    cycle_day = Column(Integer, nullable=False)
    due_days_after_end = Column(Integer, default=30)
    
    # Automation settings
    auto_generate = Column(Boolean, default=True)
    auto_send = Column(Boolean, default=False)
    batch_size = Column(Integer, default=100)
    processing_delay_minutes = Column(Integer, default=0)
    
    # Invoice settings
    invoice_template_id = Column(Integer)
    default_terms_days = Column(Integer, default=30)
    
    # Metadata
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("Administrator", foreign_keys=[created_by])

    def __repr__(self):
        return f"<BillingCycleTemplate(id={self.id}, name='{self.template_name}')>"

    def create_cycle(self, start_date, cycle_name=None):
        """Create a new billing cycle from this template"""
        if not cycle_name:
            cycle_name = f"{self.template_name} - {start_date.strftime('%Y-%m')}"
        
        # Calculate end date based on cycle type
        if self.cycle_type == BillingCycleType.MONTHLY:
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=self.cycle_day) - timedelta(days=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1, day=self.cycle_day) - timedelta(days=1)
        elif self.cycle_type == BillingCycleType.QUARTERLY:
            end_date = start_date + timedelta(days=90)
        elif self.cycle_type == BillingCycleType.ANNUAL:
            end_date = start_date.replace(year=start_date.year + 1) - timedelta(days=1)
        else:
            # Default to monthly for custom
            end_date = start_date + timedelta(days=30)
        
        # Calculate due date
        due_date = end_date + timedelta(days=self.due_days_after_end)
        
        cycle = BillingCycle(
            cycle_name=cycle_name,
            cycle_type=self.cycle_type,
            cycle_day=self.cycle_day,
            start_date=start_date,
            end_date=end_date,
            due_date=due_date,
            auto_generate=self.auto_generate,
            auto_send=self.auto_send,
            batch_size=self.batch_size,
            processing_delay_minutes=self.processing_delay_minutes
        )
        
        return cycle

    def get_template_summary(self):
        """Get template configuration summary"""
        return {
            "template_name": self.template_name,
            "cycle_type": self.cycle_type.value,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "settings": {
                "cycle_day": self.cycle_day,
                "due_days_after_end": self.due_days_after_end,
                "default_terms_days": self.default_terms_days
            },
            "automation": {
                "auto_generate": self.auto_generate,
                "auto_send": self.auto_send,
                "batch_size": self.batch_size,
                "processing_delay_minutes": self.processing_delay_minutes
            }
        }


class BillingCycleJob(Base):
    """Billing cycle processing jobs"""
    __tablename__ = "billing_cycle_jobs"

    id = Column(Integer, primary_key=True, index=True)
    billing_cycle_id = Column(Integer, ForeignKey("billing_cycles.id"), nullable=False)
    job_type = Column(String(50), nullable=False)  # generate_invoices, send_invoices, etc.
    
    # Job status
    status = Column(String(20), nullable=False, default="pending", index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Progress tracking
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    
    # Error handling
    error_log = Column(JSONB)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    job_parameters = Column(JSONB)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    billing_cycle = relationship("BillingCycle")
    creator = relationship("Administrator", foreign_keys=[created_by])

    def __repr__(self):
        return f"<BillingCycleJob(id={self.id}, type='{self.job_type}', status='{self.status}')>"

    @property
    def is_running(self):
        """Check if job is currently running"""
        return self.status == "running"

    @property
    def is_completed(self):
        """Check if job is completed"""
        return self.status == "completed"

    @property
    def is_failed(self):
        """Check if job failed"""
        return self.status == "failed"

    @property
    def progress_percentage(self):
        """Calculate job progress percentage"""
        if self.total_records == 0:
            return 0
        return (self.processed_records / self.total_records) * 100

    def start_job(self):
        """Start the job"""
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)

    def complete_job(self):
        """Mark job as completed"""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)

    def fail_job(self, error_message=None):
        """Mark job as failed"""
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        if error_message:
            self.error_log = self.error_log or []
            self.error_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": error_message
            })

    def get_job_summary(self):
        """Get job processing summary"""
        return {
            "job_type": self.job_type,
            "status": self.status,
            "progress": {
                "total_records": self.total_records,
                "processed_records": self.processed_records,
                "successful_records": self.successful_records,
                "failed_records": self.failed_records,
                "progress_percentage": self.progress_percentage
            },
            "timing": {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration": (self.completed_at - self.started_at).total_seconds() if self.started_at and self.completed_at else None
            },
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "is_running": self.is_running,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed
        }
