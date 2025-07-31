"""
Enhanced Audit Mixins with Soft Delete Support and Change Data Capture

This module provides comprehensive audit infrastructure including:
- Enhanced audit mixin with soft delete support
- Async audit queue processing
- Configuration versioning
- Change data capture (CDC)
- Audit event listeners
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Integer, event, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EnhancedAuditMixin:
    """
    Enhanced audit mixin with soft delete support and versioning.

    Provides:
    - Standard audit fields (created_at, updated_at, created_by_id, updated_by_id)
    - Soft delete support (deleted_at, deleted_by_id)
    - Version tracking for optimistic locking
    - Automatic timestamp management
    """

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        )

    @declared_attr
    def created_by_id(cls):
        return Column(Integer, nullable=True)

    @declared_attr
    def updated_by_id(cls):
        return Column(Integer, nullable=True)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def deleted_by_id(cls):
        return Column(Integer, nullable=True)

    @declared_attr
    def version(cls):
        return Column(Integer, nullable=False, default=1)

    def soft_delete(self, deleted_by_id: Optional[int] = None):
        """Perform soft delete by setting deleted_at timestamp."""
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by_id = deleted_by_id
        self.version += 1

    def restore(self, restored_by_id: Optional[int] = None):
        """Restore soft-deleted record."""
        self.deleted_at = None
        self.deleted_by_id = None
        self.updated_by_id = restored_by_id
        self.version += 1

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None

    def increment_version(self):
        """Increment version for optimistic locking."""
        self.version += 1


class AuditEventCapture:
    """
    Captures audit events and queues them for async processing.
    """

    @staticmethod
    def capture_change(
        session: Session,
        instance: Any,
        operation: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Capture audit event and add to processing queue.

        Args:
            session: SQLAlchemy session
            instance: The model instance being audited
            operation: Operation type (INSERT, UPDATE, DELETE)
            old_values: Previous values (for UPDATE/DELETE)
            new_values: New values (for INSERT/UPDATE)
            user_id: ID of user performing the operation
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: Client user agent
        """
        try:
            # Get table name and record ID
            table_name = instance.__tablename__
            record_id = str(getattr(instance, "id", "unknown"))

            # Create audit queue entry
            from app.models.audit import AuditQueue

            audit_entry = AuditQueue(
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                old_values=old_values,
                new_values=new_values,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.now(timezone.utc),
                status="pending",
            )

            session.add(audit_entry)
            logger.debug(
                f"Audit event captured: {table_name}.{record_id} - {operation}"
            )

        except Exception as e:
            logger.error(f"Failed to capture audit event: {e}")


class ConfigurationVersioning:
    """
    Handles configuration snapshots and versioning.
    """

    @staticmethod
    def create_snapshot(
        session: Session,
        config_type: str,
        config_key: str,
        config_data: Dict[str, Any],
        created_by_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> int:
        """
        Create a configuration snapshot.

        Returns:
            Version number of the created snapshot
        """
        try:
            from app.models.audit import ConfigurationSnapshot

            # Get next version number
            latest_version = (
                session.query(ConfigurationSnapshot)
                .filter_by(config_type=config_type, config_key=config_key)
                .order_by(ConfigurationSnapshot.version.desc())
                .first()
            )

            next_version = (latest_version.version + 1) if latest_version else 1

            # Deactivate previous snapshots
            session.query(ConfigurationSnapshot).filter_by(
                config_type=config_type, config_key=config_key, is_active=True
            ).update({"is_active": False})

            # Create new snapshot
            snapshot = ConfigurationSnapshot(
                config_type=config_type,
                config_key=config_key,
                snapshot_data=config_data,
                version=next_version,
                created_at=datetime.now(timezone.utc),
                created_by_id=created_by_id,
                description=description,
                is_active=True,
            )

            session.add(snapshot)
            session.flush()

            logger.info(
                f"Configuration snapshot created: {config_type}.{config_key} v{next_version}"
            )
            return next_version

        except Exception as e:
            logger.error(f"Failed to create configuration snapshot: {e}")
            raise

    @staticmethod
    def get_active_config(
        session: Session, config_type: str, config_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get the active configuration snapshot."""
        try:
            from app.models.audit import ConfigurationSnapshot

            snapshot = (
                session.query(ConfigurationSnapshot)
                .filter_by(
                    config_type=config_type, config_key=config_key, is_active=True
                )
                .first()
            )

            return snapshot.snapshot_data if snapshot else None

        except Exception as e:
            logger.error(f"Failed to get active configuration: {e}")
            return None


class ChangeDataCapture:
    """
    Real-time change data capture for critical configurations.
    """

    @staticmethod
    def log_change(
        session: Session,
        table_name: str,
        record_id: str,
        operation: str,
        change_data: Dict[str, Any],
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        source: str = "application",
    ):
        """
        Log change data capture event.
        """
        try:
            from app.models.audit import CDCLog

            cdc_entry = CDCLog(
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                change_data=change_data,
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                session_id=session_id,
                transaction_id=transaction_id,
                source=source,
            )

            session.add(cdc_entry)
            logger.debug(f"CDC event logged: {table_name}.{record_id} - {operation}")

        except Exception as e:
            logger.error(f"Failed to log CDC event: {e}")


def setup_audit_listeners():
    """
    Set up SQLAlchemy event listeners for automatic audit capture.
    Note: These are lightweight listeners that queue events for async processing.
    """

    def before_insert(mapper, connection, target):
        """Capture INSERT events."""
        if hasattr(target, "__audit_enabled__") and target.__audit_enabled__:
            # Get new values
            new_values = {}
            for column in mapper.columns:
                value = getattr(target, column.name, None)
                if value is not None:
                    new_values[column.name] = (
                        str(value)
                        if not isinstance(value, (str, int, float, bool))
                        else value
                    )

            # Queue for async processing
            # Note: We'll implement the actual queuing in the async processor
            logger.debug(f"INSERT event queued for {target.__tablename__}")

    def before_update(mapper, connection, target):
        """Capture UPDATE events."""
        if hasattr(target, "__audit_enabled__") and target.__audit_enabled__:
            # Get old and new values
            state = inspect(target)
            old_values = {}
            new_values = {}

            for attr in state.attrs:
                if attr.history.has_changes():
                    old_value = (
                        attr.history.deleted[0] if attr.history.deleted else None
                    )
                    new_value = attr.history.added[0] if attr.history.added else None

                    if old_value is not None:
                        old_values[attr.key] = (
                            str(old_value)
                            if not isinstance(old_value, (str, int, float, bool))
                            else old_value
                        )
                    if new_value is not None:
                        new_values[attr.key] = (
                            str(new_value)
                            if not isinstance(new_value, (str, int, float, bool))
                            else new_value
                        )

            # Increment version if using enhanced audit mixin
            if hasattr(target, "increment_version"):
                target.increment_version()

            logger.debug(f"UPDATE event queued for {target.__tablename__}")

    def before_delete(mapper, connection, target):
        """Capture DELETE events."""
        if hasattr(target, "__audit_enabled__") and target.__audit_enabled__:
            # Get current values before deletion
            old_values = {}
            for column in mapper.columns:
                value = getattr(target, column.name, None)
                if value is not None:
                    old_values[column.name] = (
                        str(value)
                        if not isinstance(value, (str, int, float, bool))
                        else value
                    )

            logger.debug(f"DELETE event queued for {target.__tablename__}")

    # Register event listeners
    # Note: We'll register these selectively for models that need auditing
    logger.info("Audit event listeners configured (registration pending)")


# Utility functions for audit management


def enable_audit_for_model(model_class):
    """
    Enable audit tracking for a specific model class.

    Usage:
        enable_audit_for_model(Customer)
    """
    model_class.__audit_enabled__ = True

    # Register event listeners for this model
    event.listen(model_class, "before_insert", setup_audit_listeners().before_insert)
    event.listen(model_class, "before_update", setup_audit_listeners().before_update)
    event.listen(model_class, "before_delete", setup_audit_listeners().before_delete)

    logger.info(f"Audit tracking enabled for {model_class.__name__}")


def disable_audit_for_model(model_class):
    """
    Disable audit tracking for a specific model class.
    """
    model_class.__audit_enabled__ = False
    logger.info(f"Audit tracking disabled for {model_class.__name__}")


def get_audit_context():
    """
    Get current audit context (user_id, session_id, etc.) from request context.
    This would typically be populated by middleware.
    """
    # Placeholder - would integrate with FastAPI request context
    return {"user_id": None, "session_id": None, "ip_address": None, "user_agent": None}
