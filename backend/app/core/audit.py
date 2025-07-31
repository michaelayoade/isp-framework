"""
Audit trail functionality for ISP Framework.

Provides SQLAlchemy mixins and utilities for tracking data changes.
"""
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect

from app.core.database import Base
from app.core.observability import log_audit_event


class AuditMixin:
    """Mixin to add audit fields to models."""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), default=datetime.now(timezone.utc), 
                     onupdate=datetime.now(timezone.utc), nullable=False)
    
    @declared_attr
    def created_by_id(cls):
        return Column(Integer, ForeignKey('administrators.id'), nullable=True)
    
    @declared_attr
    def updated_by_id(cls):
        return Column(Integer, ForeignKey('administrators.id'), nullable=True)
    
    @declared_attr
    def created_by(cls):
        return relationship("Administrator", foreign_keys=[cls.created_by_id], 
                          post_update=True, viewonly=True)
    
    @declared_attr
    def updated_by(cls):
        return relationship("Administrator", foreign_keys=[cls.updated_by_id], 
                          post_update=True, viewonly=True)


class AuditLog(Base):
    """Audit log table for tracking all data changes."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    operation = Column(String(10), nullable=False)  # CREATE, UPDATE, DELETE
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changed_fields = Column(JSON, nullable=True)
    actor_id = Column(Integer, ForeignKey('administrators.id'), nullable=True)
    actor_type = Column(String(50), nullable=True)  # admin, system, api_client
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(36), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    
    # Relationship to administrator
    actor = relationship("Administrator", foreign_keys=[actor_id], viewonly=True)
    
    def __repr__(self):
        return f"<AuditLog(table={self.table_name}, record_id={self.record_id}, op={self.operation})>"


def get_model_changes(instance, operation: str) -> Dict[str, Any]:
    """Extract changes from a SQLAlchemy model instance."""
    changes = {
        "table_name": instance.__tablename__,
        "record_id": str(getattr(instance, 'id', 'unknown')),
        "operation": operation,
        "old_values": {},
        "new_values": {},
        "changed_fields": []
    }
    
    if operation == "CREATE":
        # For new records, all fields are "new"
        state = inspect(instance)
        for attr in state.attrs:
            if not attr.key.startswith('_'):
                value = getattr(instance, attr.key, None)
                if value is not None:
                    changes["new_values"][attr.key] = serialize_value(value)
                    changes["changed_fields"].append(attr.key)
    
    elif operation == "UPDATE":
        # For updates, track what changed
        state = inspect(instance)
        for attr in state.attrs:
            if attr.history.has_changes():
                old_value = attr.history.deleted[0] if attr.history.deleted else None
                new_value = attr.history.added[0] if attr.history.added else None
                
                changes["old_values"][attr.key] = serialize_value(old_value)
                changes["new_values"][attr.key] = serialize_value(new_value)
                changes["changed_fields"].append(attr.key)
    
    elif operation == "DELETE":
        # For deletes, capture the final state
        state = inspect(instance)
        for attr in state.attrs:
            if not attr.key.startswith('_'):
                value = getattr(instance, attr.key, None)
                if value is not None:
                    changes["old_values"][attr.key] = serialize_value(value)
    
    return changes


def serialize_value(value: Any) -> Any:
    """Serialize a value for JSON storage in audit log."""
    if value is None:
        return None
    elif isinstance(value, datetime):
        return value.isoformat()
    elif hasattr(value, '__dict__'):
        # For model instances, just store the ID
        return {"id": getattr(value, 'id', None), "type": type(value).__name__}
    else:
        try:
            # Try to JSON serialize
            import json
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            return str(value)


def create_audit_log(instance, operation: str, actor_id: Optional[int] = None, 
                    actor_type: str = "system", ip_address: Optional[str] = None,
                    user_agent: Optional[str] = None, request_id: Optional[str] = None):
    """Create an audit log entry for a model change."""
    from app.core.database import SessionLocal
    
    changes = get_model_changes(instance, operation)
    
    audit_entry = AuditLog(
        table_name=changes["table_name"],
        record_id=changes["record_id"],
        operation=operation,
        old_values=changes["old_values"],
        new_values=changes["new_values"],
        changed_fields=changes["changed_fields"],
        actor_id=actor_id,
        actor_type=actor_type,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id
    )
    
    # Save to database
    db = SessionLocal()
    try:
        db.add(audit_entry)
        db.commit()
        
        # Also log to structured logs
        log_audit_event(
            domain="data_change",
            event=f"{changes['table_name']}.{operation.lower()}",
            table_name=changes["table_name"],
            record_id=changes["record_id"],
            operation=operation,
            changed_fields=changes["changed_fields"],
            actor_id=actor_id,
            actor_type=actor_type,
            request_id=request_id
        )
        
    except Exception as e:
        db.rollback()
        # Log the error but don't fail the main operation
        log_audit_event(
            domain="audit_error",
            event="audit_log_failed",
            error=str(e),
            table_name=changes["table_name"],
            record_id=changes["record_id"],
            operation=operation
        )
    finally:
        db.close()


# SQLAlchemy event listeners for automatic audit logging
# TEMPORARILY DISABLED to resolve connection pool issues
# @listens_for(Base, 'after_insert', propagate=True)
# def audit_insert(mapper, connection, target):
#     """Audit trail for INSERT operations."""
#     if hasattr(target, '__tablename__'):
#         create_audit_log(target, "CREATE")


# @listens_for(Base, 'after_update', propagate=True)
# def audit_update(mapper, connection, target):
#     """Audit trail for UPDATE operations."""
#     if hasattr(target, '__tablename__'):
#         create_audit_log(target, "UPDATE")


# @listens_for(Base, 'after_delete', propagate=True)
# def audit_delete(mapper, connection, target):
#     """Audit trail for DELETE operations."""
#     if hasattr(target, '__tablename__'):
#         create_audit_log(target, "DELETE")


def get_audit_trail(table_name: str, record_id: str, limit: int = 100) -> list:
    """Get audit trail for a specific record."""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        return db.query(AuditLog).filter(
            AuditLog.table_name == table_name,
            AuditLog.record_id == str(record_id)
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    finally:
        db.close()


def get_user_activity(actor_id: int, limit: int = 100) -> list:
    """Get recent activity for a specific user."""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        return db.query(AuditLog).filter(
            AuditLog.actor_id == actor_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    finally:
        db.close()
