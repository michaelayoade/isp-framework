"""
Audit Models for Enhanced Data Integrity and Change Tracking

This module defines the database models for the enhanced audit system:
- AuditQueue: Async audit event processing queue
- ConfigurationSnapshot: Configuration versioning and snapshots
- CDCLog: Change data capture logging
- AuditProcessingStatus: Audit processor status tracking
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from app.core.database import Base


class AuditQueue(Base):
    """
    Queue for async audit event processing.
    
    Stores audit events for background processing to avoid blocking
    main application operations.
    """
    __tablename__ = "audit_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    operation = Column(String(20), nullable=False)  # INSERT, UPDATE, DELETE
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    user_id = Column(Integer, nullable=True)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 support
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f"<AuditQueue(id={self.id}, table={self.table_name}, record={self.record_id}, operation={self.operation}, status={self.status})>"
    
    def mark_processing(self):
        """Mark audit entry as being processed."""
        self.status = 'processing'
        self.processed_at = datetime.now(timezone.utc)
    
    def mark_completed(self):
        """Mark audit entry as successfully processed."""
        self.status = 'completed'
        self.processed_at = datetime.now(timezone.utc)
    
    def mark_failed(self, error_message: str):
        """Mark audit entry as failed with error message."""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.processed_at = datetime.now(timezone.utc)
    
    def can_retry(self, max_retries: int = 3) -> bool:
        """Check if audit entry can be retried."""
        return self.retry_count < max_retries and self.status == 'failed'


class ConfigurationSnapshot(Base):
    """
    Configuration snapshots for versioning critical settings.
    
    Maintains historical versions of configuration data for
    rollback and audit purposes.
    """
    __tablename__ = "configuration_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    config_type = Column(String(50), nullable=False, index=True)  # billing, network, service, etc.
    config_key = Column(String(100), nullable=False, index=True)  # specific config identifier
    snapshot_data = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    def __repr__(self):
        return f"<ConfigurationSnapshot(id={self.id}, type={self.config_type}, key={self.config_key}, version={self.version}, active={self.is_active})>"
    
    def deactivate(self):
        """Deactivate this configuration snapshot."""
        self.is_active = False
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a specific value from the snapshot data."""
        return self.snapshot_data.get(key, default)


class CDCLog(Base):
    """
    Change Data Capture log for real-time change tracking.
    
    Captures all changes to critical data for compliance,
    auditing, and real-time monitoring.
    """
    __tablename__ = "cdc_log"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    operation = Column(String(20), nullable=False, index=True)  # INSERT, UPDATE, DELETE
    change_data = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = Column(Integer, nullable=True)
    session_id = Column(String(100), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    source = Column(String(50), nullable=False, default='application')  # application, migration, system, etc.
    
    def __repr__(self):
        return f"<CDCLog(id={self.id}, table={self.table_name}, record={self.record_id}, operation={self.operation}, timestamp={self.timestamp})>"
    
    def get_changed_fields(self) -> list:
        """Get list of fields that were changed."""
        if self.operation == 'UPDATE' and 'changes' in self.change_data:
            return list(self.change_data['changes'].keys())
        return []
    
    def get_old_value(self, field: str) -> Any:
        """Get old value for a specific field."""
        if self.operation == 'UPDATE' and 'changes' in self.change_data:
            return self.change_data['changes'].get(field, {}).get('old')
        return None
    
    def get_new_value(self, field: str) -> Any:
        """Get new value for a specific field."""
        if self.operation == 'UPDATE' and 'changes' in self.change_data:
            return self.change_data['changes'].get(field, {}).get('new')
        elif self.operation == 'INSERT' and 'data' in self.change_data:
            return self.change_data['data'].get(field)
        return None


class AuditProcessingStatus(Base):
    """
    Status tracking for audit processors.
    
    Monitors the health and progress of async audit processors
    to ensure reliable audit processing.
    """
    __tablename__ = "audit_processing_status"
    
    id = Column(Integer, primary_key=True, index=True)
    processor_name = Column(String(100), nullable=False, unique=True, index=True)
    last_processed_id = Column(Integer, nullable=True)
    last_processed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default='active')  # active, paused, error, stopped
    error_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<AuditProcessingStatus(id={self.id}, processor={self.processor_name}, status={self.status}, last_processed={self.last_processed_id})>"
    
    def update_progress(self, last_processed_id: int):
        """Update processing progress."""
        self.last_processed_id = last_processed_id
        self.last_processed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_error(self, error_message: str):
        """Mark processor as having an error."""
        self.status = 'error'
        self.error_count += 1
        self.last_error = error_message
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_active(self):
        """Mark processor as active and clear errors."""
        self.status = 'active'
        self.last_error = None
        self.updated_at = datetime.now(timezone.utc)
    
    def is_healthy(self, max_error_count: int = 10) -> bool:
        """Check if processor is healthy."""
        return self.status == 'active' and self.error_count < max_error_count
    
    def get_processing_lag(self) -> Optional[int]:
        """Get processing lag in seconds since last processing."""
        if self.last_processed_at:
            return int((datetime.now(timezone.utc) - self.last_processed_at).total_seconds())
        return None


# Utility functions for audit models

def get_pending_audit_count(session) -> int:
    """Get count of pending audit entries."""
    return session.query(AuditQueue).filter_by(status='pending').count()


def get_failed_audit_count(session) -> int:
    """Get count of failed audit entries."""
    return session.query(AuditQueue).filter_by(status='failed').count()


def get_audit_processing_stats(session) -> Dict[str, Any]:
    """Get comprehensive audit processing statistics."""
    stats = {
        'pending_count': session.query(AuditQueue).filter_by(status='pending').count(),
        'processing_count': session.query(AuditQueue).filter_by(status='processing').count(),
        'completed_count': session.query(AuditQueue).filter_by(status='completed').count(),
        'failed_count': session.query(AuditQueue).filter_by(status='failed').count(),
        'total_count': session.query(AuditQueue).count(),
        'active_processors': session.query(AuditProcessingStatus).filter_by(status='active').count(),
        'error_processors': session.query(AuditProcessingStatus).filter_by(status='error').count(),
    }
    
    # Calculate processing rates
    if stats['total_count'] > 0:
        stats['completion_rate'] = round((stats['completed_count'] / stats['total_count']) * 100, 2)
        stats['failure_rate'] = round((stats['failed_count'] / stats['total_count']) * 100, 2)
    else:
        stats['completion_rate'] = 0.0
        stats['failure_rate'] = 0.0
    
    return stats


def cleanup_old_audit_entries(session, days_to_keep: int = 90):
    """Clean up old completed audit entries."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    
    deleted_count = session.query(AuditQueue)\
        .filter(AuditQueue.status == 'completed')\
        .filter(AuditQueue.processed_at < cutoff_date)\
        .delete()
    
    return deleted_count


def get_configuration_history(session, config_type: str, config_key: str, limit: int = 10):
    """Get configuration change history."""
    return session.query(ConfigurationSnapshot)\
        .filter_by(config_type=config_type, config_key=config_key)\
        .order_by(ConfigurationSnapshot.version.desc())\
        .limit(limit)\
        .all()


def get_recent_changes(session, table_name: str = None, hours: int = 24, limit: int = 100):
    """Get recent changes from CDC log."""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    query = session.query(CDCLog)\
        .filter(CDCLog.timestamp >= cutoff_time)\
        .order_by(CDCLog.timestamp.desc())
    
    if table_name:
        query = query.filter_by(table_name=table_name)
    
    return query.limit(limit).all()
