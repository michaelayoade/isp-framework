"""
File Storage Models for MinIO S3 Integration

Handles file storage, customer document management, CSV imports, ticket media uploads,
and configuration backups with MinIO S3-compatible storage.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.core.database import Base


class FileCategory(PyEnum):
    CUSTOMER_DOCUMENT = "customer_document"
    TICKET_ATTACHMENT = "ticket_attachment"
    CUSTOMER_IMPORT = "customer_import"
    SERVICE_EXPORT = "service_export"
    CONFIG_BACKUP = "config_backup"
    SYSTEM_FILE = "system_file"


class FileStatus(PyEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class ImportStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileMetadata(Base):
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_category = Column(Enum(FileCategory), nullable=False)
    file_status = Column(Enum(FileStatus), default=FileStatus.UPLOADED)
    
    # Relationships
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("administrators.id"), nullable=False)
    
    # Storage info
    bucket_name = Column(String(100), nullable=False)
    object_key = Column(String(500), nullable=False)
    presigned_url = Column(String(1000), nullable=True)
    url_expires_at = Column(DateTime, nullable=True)
    
    # File metadata
    file_metadata = Column(JSON, default={})
    checksum = Column(String(64), nullable=True)  # SHA256 hash
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="files")
    ticket = relationship("Ticket", back_populates="file_attachments")
    uploaded_by_admin = relationship("Administrator")
    permissions = relationship("FilePermission", back_populates="file_metadata", cascade="all, delete-orphan")


class ImportJob(Base):
    __tablename__ = "import_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(255), nullable=False)
    file_metadata_id = Column(Integer, ForeignKey("file_metadata.id"), nullable=False)
    import_type = Column(String(50), nullable=False)  # 'customer_csv', 'service_csv', etc.
    
    # Status tracking
    status = Column(Enum(ImportStatus), default=ImportStatus.PENDING)
    progress_percent = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    
    # Processing details
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    validation_errors = Column(JSON, default=[])
    
    # Configuration
    import_config = Column(JSON, default={})  # skip_errors, update_existing, etc.
    
    # Relationships
    file_metadata = relationship("FileMetadata")
    created_by = Column(Integer, ForeignKey("administrators.id"), nullable=False)
    created_by_admin = relationship("Administrator")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ExportJob(Base):
    __tablename__ = "export_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(255), nullable=False)
    export_type = Column(String(50), nullable=False)  # 'customer_export', 'billing_export', etc.
    
    # Configuration
    export_config = Column(JSON, default={})  # filters, columns, format
    file_format = Column(String(10), default="csv")  # csv, xlsx, json
    
    # Status tracking
    status = Column(Enum(ImportStatus), default=ImportStatus.PENDING)
    progress_percent = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    
    # File info
    output_file_metadata_id = Column(Integer, ForeignKey("file_metadata.id"), nullable=True)
    output_file_metadata = relationship("FileMetadata", foreign_keys=[output_file_metadata_id])
    
    # Processing details
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    created_by = Column(Integer, ForeignKey("administrators.id"), nullable=False)
    created_by_admin = relationship("Administrator")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FilePermission(Base):
    __tablename__ = "file_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    file_metadata_id = Column(Integer, ForeignKey("file_metadata.id"), nullable=False)
    
    # Access control
    is_public = Column(Boolean, default=False)
    allowed_customers = Column(JSON, default=[])  # List of customer IDs
    allowed_roles = Column(JSON, default=[])  # List of role names
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    file_metadata = relationship("FileMetadata", back_populates="permissions")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Add relationships to existing models
# These will be added via migration scripts
