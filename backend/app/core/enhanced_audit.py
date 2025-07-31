"""
Enhanced Audit Trail functionality for ISP Framework.

Provides comprehensive audit mixins with soft delete support,
optimized audit processing, and Change Data Capture capabilities.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict, List
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, Index
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect
from enum import Enum
import json

from app.core.database import Base
from app.core.observability import log_audit_event


class AuditOperationType(str, Enum):
    """Types of audit operations."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SOFT_DELETE = "SOFT_DELETE"
    RESTORE = "RESTORE"
    ARCHIVE = "ARCHIVE"


class EnhancedAuditMixin:
    """Enhanced mixin with comprehensive audit fields including soft delete support."""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), default=datetime.now(timezone.utc), 
                     onupdate=datetime.now(timezone.utc), nullable=False, index=True)
    
    @declared_attr
    def created_by_id(cls):
        return Column(Integer, ForeignKey('administrators.id'), nullable=True, index=True)
    
    @declared_attr
    def updated_by_id(cls):
        return Column(Integer, ForeignKey('administrators.id'), nullable=True, index=True)
    
    # Soft Delete Support
    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True, index=True)
    
    @declared_attr
    def deleted_by_id(cls):
        return Column(Integer, ForeignKey('administrators.id'), nullable=True, index=True)
    
    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False, index=True)
    
    # Version Control
    @declared_attr
    def version(cls):
        return Column(Integer, default=1, nullable=False)
    
    # Relationships
    @declared_attr
    def created_by(cls):
        return relationship("Administrator", foreign_keys=[cls.created_by_id], 
                          post_update=True, viewonly=True)
    
    @declared_attr
    def updated_by(cls):
        return relationship("Administrator", foreign_keys=[cls.updated_by_id], 
                          post_update=True, viewonly=True)
    
    @declared_attr
    def deleted_by(cls):
        return relationship("Administrator", foreign_keys=[cls.deleted_by_id], 
                          post_update=True, viewonly=True)
    
    def soft_delete(self, deleted_by_id: Optional[int] = None):
        """Perform soft delete on the record."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by_id = deleted_by_id
        self.version += 1
    
    def restore(self, restored_by_id: Optional[int] = None):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by_id = None
        self.updated_by_id = restored_by_id
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1
    
    @classmethod
    def active_only(cls):
        """Query filter for non-deleted records."""
        return cls.is_deleted is False
    
    @classmethod
    def deleted_only(cls):
        """Query filter for deleted records."""
        return cls.is_deleted is True


class EnhancedAuditLog(Base):
    """Enhanced audit log table with improved performance and features."""
    
    __tablename__ = "enhanced_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    operation = Column(String(20), nullable=False, index=True)  # CREATE, UPDATE, DELETE, SOFT_DELETE, RESTORE
    
    # Change Details
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changed_fields = Column(JSON, nullable=True)
    field_count = Column(Integer, default=0)  # Number of fields changed
    
    # Actor Information
    actor_id = Column(Integer, ForeignKey('administrators.id'), nullable=True, index=True)
    actor_type = Column(String(50), nullable=True, index=True)  # admin, system, api_client, customer
    actor_name = Column(String(255), nullable=True)  # Denormalized for performance
    
    # Request Context
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(36), nullable=True, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    
    # Business Context
    business_reason = Column(String(500), nullable=True)
    compliance_category = Column(String(100), nullable=True, index=True)  # GDPR, SOX, PCI, etc.
    risk_level = Column(String(20), nullable=True, index=True)  # low, medium, high, critical
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    processing_time_ms = Column(Integer, nullable=True)  # Time taken to process change
    
    # Metadata
    version_before = Column(Integer, nullable=True)
    version_after = Column(Integer, nullable=True)
    batch_id = Column(String(36), nullable=True, index=True)  # For bulk operations
    
    # Relationships
    actor = relationship("Administrator", foreign_keys=[actor_id], viewonly=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_table_record', 'table_name', 'record_id'),
        Index('idx_audit_timestamp_table', 'timestamp', 'table_name'),
        Index('idx_audit_actor_timestamp', 'actor_id', 'timestamp'),
        Index('idx_audit_operation_timestamp', 'operation', 'timestamp'),
        Index('idx_audit_compliance', 'compliance_category', 'timestamp'),
        Index('idx_audit_risk_level', 'risk_level', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<EnhancedAuditLog(table={self.table_name}, record_id={self.record_id}, op={self.operation})>"


class ConfigurationSnapshot(Base):
    """Configuration snapshots for critical system settings."""
    
    __tablename__ = "configuration_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    snapshot_name = Column(String(255), nullable=False, index=True)
    snapshot_type = Column(String(50), nullable=False, index=True)  # manual, scheduled, pre_change, rollback
    
    # Configuration Data
    configuration_data = Column(JSON, nullable=False)
    configuration_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # For categorization
    
    # Versioning
    version = Column(String(20), nullable=True)
    previous_snapshot_id = Column(Integer, ForeignKey('configuration_snapshots.id'), nullable=True)
    
    # Audit Fields
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey('administrators.id'), nullable=True)
    
    # Lifecycle
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    created_by = relationship("Administrator", viewonly=True)
    previous_snapshot = relationship("ConfigurationSnapshot", remote_side=[id], viewonly=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_config_snapshot_type_date', 'snapshot_type', 'created_at'),
        Index('idx_config_snapshot_hash', 'configuration_hash'),
        Index('idx_config_snapshot_active', 'is_active', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ConfigurationSnapshot(name={self.snapshot_name}, type={self.snapshot_type})>"


class AuditQueue(Base):
    """Queue for async audit processing to prevent connection pool exhaustion."""
    
    __tablename__ = "audit_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    operation = Column(String(20), nullable=False)
    
    # Audit Data (JSON serialized)
    audit_data = Column(JSON, nullable=False)
    
    # Processing Status
    status = Column(String(20), default='pending', nullable=False, index=True)  # pending, processing, completed, failed
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Timing
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Priority
    priority = Column(Integer, default=5, nullable=False, index=True)  # 1=highest, 10=lowest
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_queue_status_priority', 'status', 'priority', 'created_at'),
        Index('idx_audit_queue_retry', 'next_retry_at', 'status'),
        Index('idx_audit_queue_table_record', 'table_name', 'record_id'),
    )
    
    def __repr__(self):
        return f"<AuditQueue(table={self.table_name}, record_id={self.record_id}, status={self.status})>"


# Async Audit Processing Functions
class AsyncAuditProcessor:
    """Async processor for audit queue to prevent connection pool issues."""
    
    @staticmethod
    async def queue_audit_event(
        table_name: str,
        record_id: str,
        operation: str,
        audit_data: Dict[str, Any],
        priority: int = 5
    ):
        """Queue an audit event for async processing."""
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            queue_item = AuditQueue(
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                audit_data=audit_data,
                priority=priority
            )
            db.add(queue_item)
            db.commit()
        except Exception as e:
            db.rollback()
            # Log error but don't fail the main operation
            log_audit_event("audit_queue_error", {"error": str(e), "table": table_name})
        finally:
            db.close()
    
    @staticmethod
    async def process_audit_queue(batch_size: int = 100):
        """Process pending audit events from queue."""
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            # Get pending items ordered by priority and creation time
            pending_items = db.query(AuditQueue).filter(
                AuditQueue.status == 'pending'
            ).order_by(
                AuditQueue.priority.asc(),
                AuditQueue.created_at.asc()
            ).limit(batch_size).all()
            
            for item in pending_items:
                try:
                    # Mark as processing
                    item.status = 'processing'
                    db.commit()
                    
                    # Create audit log entry
                    audit_log = EnhancedAuditLog(**item.audit_data)
                    db.add(audit_log)
                    
                    # Mark as completed
                    item.status = 'completed'
                    item.processed_at = datetime.now(timezone.utc)
                    db.commit()
                    
                except Exception as e:
                    # Handle retry logic
                    item.retry_count += 1
                    if item.retry_count >= item.max_retries:
                        item.status = 'failed'
                        item.error_message = str(e)
                    else:
                        item.status = 'pending'
                        item.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5 * item.retry_count)
                    
                    db.commit()
                    
        except Exception as e:
            db.rollback()
            log_audit_event("audit_processor_error", {"error": str(e)})
        finally:
            db.close()


# Enhanced audit event creation with async queuing
async def create_enhanced_audit_log(
    instance,
    operation: str,
    actor_id: Optional[int] = None,
    actor_type: str = "system",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    business_reason: Optional[str] = None,
    compliance_category: Optional[str] = None,
    risk_level: str = "low"
):
    """Create an enhanced audit log entry with async processing."""
    
    # Extract model changes
    changes = get_enhanced_model_changes(instance, operation)
    
    # Prepare audit data
    audit_data = {
        "table_name": instance.__tablename__,
        "record_id": str(getattr(instance, 'id', 'unknown')),
        "operation": operation,
        "old_values": changes.get('old_values'),
        "new_values": changes.get('new_values'),
        "changed_fields": changes.get('changed_fields'),
        "field_count": len(changes.get('changed_fields', [])),
        "actor_id": actor_id,
        "actor_type": actor_type,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "request_id": request_id,
        "business_reason": business_reason,
        "compliance_category": compliance_category,
        "risk_level": risk_level,
        "version_before": getattr(instance, 'version', None) - 1 if hasattr(instance, 'version') else None,
        "version_after": getattr(instance, 'version', None),
        "timestamp": datetime.now(timezone.utc)
    }
    
    # Queue for async processing
    await AsyncAuditProcessor.queue_audit_event(
        table_name=instance.__tablename__,
        record_id=str(getattr(instance, 'id', 'unknown')),
        operation=operation,
        audit_data=audit_data,
        priority=1 if risk_level == "critical" else 3 if risk_level == "high" else 5
    )


def get_enhanced_model_changes(instance, operation: str) -> Dict[str, Any]:
    """Extract enhanced changes from a SQLAlchemy model instance."""
    
    mapper = inspect(instance.__class__)
    changes = {
        'old_values': {},
        'new_values': {},
        'changed_fields': []
    }
    
    if operation == "CREATE":
        for column in mapper.columns:
            value = getattr(instance, column.name, None)
            if value is not None:
                changes['new_values'][column.name] = serialize_enhanced_value(value)
                changes['changed_fields'].append(column.name)
                
    elif operation in ["UPDATE", "SOFT_DELETE", "RESTORE"]:
        # Get the current state
        state = inspect(instance)
        
        for attr in state.attrs:
            if attr.history.has_changes():
                old_value = attr.history.deleted[0] if attr.history.deleted else None
                new_value = attr.history.added[0] if attr.history.added else getattr(instance, attr.key)
                
                changes['old_values'][attr.key] = serialize_enhanced_value(old_value)
                changes['new_values'][attr.key] = serialize_enhanced_value(new_value)
                changes['changed_fields'].append(attr.key)
                
    elif operation == "DELETE":
        for column in mapper.columns:
            value = getattr(instance, column.name, None)
            if value is not None:
                changes['old_values'][column.name] = serialize_enhanced_value(value)
                changes['changed_fields'].append(column.name)
    
    return changes


def serialize_enhanced_value(value: Any) -> Any:
    """Enhanced value serialization for JSON storage in audit log."""
    if value is None:
        return None
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, Enum):
        return value.value
    elif hasattr(value, '__dict__'):
        # For complex objects, store a summary
        return {
            'type': value.__class__.__name__,
            'id': getattr(value, 'id', None),
            'repr': str(value)[:200]  # Truncate long representations
        }
    else:
        return str(value)


# Configuration Snapshot Management
class ConfigurationManager:
    """Manager for configuration snapshots and versioning."""
    
    @staticmethod
    def create_snapshot(
        name: str,
        snapshot_type: str,
        configuration_data: Dict[str, Any],
        description: Optional[str] = None,
        created_by_id: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> ConfigurationSnapshot:
        """Create a configuration snapshot."""
        from app.core.database import SessionLocal
        import hashlib
        
        # Calculate configuration hash
        config_json = json.dumps(configuration_data, sort_keys=True)
        config_hash = hashlib.sha256(config_json.encode()).hexdigest()
        
        db = SessionLocal()
        try:
            snapshot = ConfigurationSnapshot(
                snapshot_name=name,
                snapshot_type=snapshot_type,
                configuration_data=configuration_data,
                configuration_hash=config_hash,
                description=description,
                created_by_id=created_by_id,
                tags=tags or []
            )
            
            db.add(snapshot)
            db.commit()
            db.refresh(snapshot)
            return snapshot
            
        finally:
            db.close()
    
    @staticmethod
    def get_latest_snapshot(snapshot_type: str) -> Optional[ConfigurationSnapshot]:
        """Get the latest snapshot of a specific type."""
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            return db.query(ConfigurationSnapshot).filter(
                ConfigurationSnapshot.snapshot_type == snapshot_type,
                ConfigurationSnapshot.is_active is True
            ).order_by(ConfigurationSnapshot.created_at.desc()).first()
        finally:
            db.close()
    
    @staticmethod
    def rollback_to_snapshot(snapshot_id: int, rolled_back_by_id: Optional[int] = None) -> bool:
        """Rollback configuration to a specific snapshot."""
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            snapshot = db.query(ConfigurationSnapshot).filter(
                ConfigurationSnapshot.id == snapshot_id
            ).first()
            
            if not snapshot:
                return False
            
            # Create a new snapshot with the rollback data
            rollback_snapshot = ConfigurationSnapshot(
                snapshot_name=f"Rollback to {snapshot.snapshot_name}",
                snapshot_type="rollback",
                configuration_data=snapshot.configuration_data,
                configuration_hash=snapshot.configuration_hash,
                description=f"Rollback to snapshot {snapshot_id}",
                created_by_id=rolled_back_by_id,
                previous_snapshot_id=snapshot_id
            )
            
            db.add(rollback_snapshot)
            db.commit()
            
            # Here you would implement the actual configuration application
            # This depends on your specific configuration management needs
            
            return True
            
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()
