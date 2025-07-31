"""
Foundation Base Models

Core foundational models that support the entire ISP Framework including
locations, file storage, and reseller management.
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DECIMAL

from app.core.database import Base


class Location(Base):
    """Geographic locations for customers and infrastructure"""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True)
    description = Column(Text)

    # Geographic Information
    country = Column(String(100), default="Nigeria")
    state_province = Column(String(100))
    city = Column(String(100))
    postal_code = Column(String(20))

    # Coordinates
    latitude = Column(String(20))
    longitude = Column(String(20))

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    routers = relationship("Router", back_populates="location")
    network_devices = relationship("ManagedDevice", back_populates="location")


class Reseller(Base):
    """Reseller partners who manage customers under the main ISP"""

    __tablename__ = "resellers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True)

    # Contact Information
    contact_person = Column(String(255))
    email = Column(String(255), nullable=False)
    phone = Column(String(50))

    # Address
    address = Column(String(500))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="Nigeria")

    # Business Information
    tax_id = Column(String(100))
    registration_number = Column(String(100))

    # Reseller Business Terms
    commission_percentage = Column(DECIMAL(5, 2), default=0)  # % of customer payments
    territory = Column(String(255))  # Geographic territory restriction
    customer_limit = Column(Integer)  # Maximum customers allowed

    # Authentication
    password_hash = Column(String(255))  # Hashed password for reseller login
    last_login = Column(DateTime(timezone=True))  # Last login timestamp

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customers = relationship("Customer", back_populates="reseller")
    # Portal configuration entries (one reseller can have many configs)
    portal_configs = relationship(
        "PortalConfig", back_populates="reseller", cascade="all, delete-orphan"
    )
    # API keys for reseller API access
    api_keys = relationship(
        "APIKey", back_populates="reseller", cascade="all, delete-orphan"
    )


class FileStorage(Base):
    """File storage and management"""

    __tablename__ = "file_storage"

    id = Column(Integer, primary_key=True, index=True)
    filename_original = Column(String(255), nullable=False)
    filename_stored = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    file_hash = Column(String(64), index=True)

    # Storage Configuration
    storage_type = Column(String(50), default="local")  # local, s3, minio, etc.
    storage_bucket = Column(String(100))
    storage_region = Column(String(50))

    # Metadata
    description = Column(Text)
    tags = Column(JSON, default=list)

    # Access Control
    is_public = Column(Boolean, default=False)
    access_level = Column(String(50), default="private")  # private, public, restricted

    # Upload Information
    uploaded_by = Column(Integer)  # ID of uploader
    uploaded_by_type = Column(String(20), default="admin")  # admin, customer, system

    # Security
    is_active = Column(Boolean, default=True)
    is_virus_scanned = Column(Boolean, default=False)
    virus_scan_result = Column(String(50))  # clean, infected, unknown

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True))

    # Relationships
    customer_documents = relationship("CustomerDocument", back_populates="file")


class DeadLetterQueue(Base):
    """Dead letter queue for failed background tasks"""

    __tablename__ = "dead_letter_queue"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), nullable=False, index=True)
    task_name = Column(String(255), nullable=False, index=True)
    queue_name = Column(String(100), nullable=False, default="default")

    # Task data
    task_args = Column(Text)  # JSON serialized args
    task_kwargs = Column(Text)  # JSON serialized kwargs

    # Error information
    exception_type = Column(String(255))
    exception_message = Column(Text)
    traceback = Column(Text)

    # Processing information
    retry_count = Column(Integer, default=0)
    failed_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        String(50), default="pending", index=True
    )  # pending, requeued, failed, processed, error

    # Processing timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    requeued_at = Column(DateTime(timezone=True))

    # Additional metadata
    priority = Column(Integer, default=0)
    notes = Column(Text)


class TaskExecutionLog(Base):
    """Log of task executions for monitoring and debugging"""

    __tablename__ = "task_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), nullable=False, index=True)
    task_name = Column(String(255), nullable=False, index=True)

    # Execution details
    status = Column(String(50), nullable=False, index=True)  # success, failed, retry
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Float)

    # Results
    result = Column(Text)  # Truncated result for successful tasks
    error = Column(Text)  # Error message for failed tasks

    # Metadata
    worker_name = Column(String(255))
    queue_name = Column(String(100))
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
