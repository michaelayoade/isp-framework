"""
Provisioning Queue Models

Database models for async service provisioning including:
- Provisioning job queue with retry logic
- Job status tracking and history
- Idempotency and error handling
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from datetime import datetime, timezone
import uuid


class ProvisioningJob(Base):
    """Provisioning job queue for async service provisioning."""
    __tablename__ = "provisioning_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Service information
    service_id = Column(Integer, nullable=False, index=True)
    service_type = Column(String(50), nullable=False, index=True)  # internet, voice, bundle
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    
    # Job configuration
    priority = Column(String(20), default="normal", index=True)  # low, normal, high, urgent
    scheduled_for = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    auto_activate = Column(Boolean, default=True)
    
    # Job status
    status = Column(String(50), default="queued", index=True)  # queued, processing, completed, failed, cancelled
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Provisioning parameters (JSON)
    parameters = Column(JSON, nullable=True)  # router_id, ip_pool_id, vlan_id, etc.
    
    # Execution tracking
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results and errors
    result_data = Column(JSON, nullable=True)  # assigned_ip, router_config, etc.
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="provisioning_jobs")
    created_by_admin = relationship("Administrator")
    job_history = relationship("ProvisioningJobHistory", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ProvisioningJob(id={self.id}, job_id='{self.job_id}', service_type='{self.service_type}', status='{self.status}')>"


class ProvisioningJobHistory(Base):
    """History log for provisioning job status changes."""
    __tablename__ = "provisioning_job_history"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("provisioning_jobs.id"), nullable=False, index=True)
    
    # Status change
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    
    # Change details
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    
    # Relationships
    job = relationship("ProvisioningJob", back_populates="job_history")
    created_by_admin = relationship("Administrator")

    def __repr__(self):
        return f"<ProvisioningJobHistory(id={self.id}, job_id={self.job_id}, status_change='{self.old_status}' -> '{self.new_status}')>"


class ProvisioningWorkerStatus(Base):
    """Status tracking for provisioning workers."""
    __tablename__ = "provisioning_worker_status"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(255), unique=True, index=True)
    worker_name = Column(String(255), nullable=False)
    
    # Worker status
    status = Column(String(50), default="idle")  # idle, busy, offline, error
    current_job_id = Column(String(255), nullable=True)
    
    # Performance metrics
    jobs_processed = Column(Integer, default=0)
    jobs_succeeded = Column(Integer, default=0)
    jobs_failed = Column(Integer, default=0)
    
    # Health tracking
    last_heartbeat = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_job_started = Column(DateTime(timezone=True), nullable=True)
    last_job_completed = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    max_concurrent_jobs = Column(Integer, default=1)
    supported_service_types = Column(JSON, nullable=True)  # ["internet", "voice", "bundle"]
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ProvisioningWorkerStatus(id={self.id}, worker_id='{self.worker_id}', status='{self.status}')>"
