"""
Audit Management API Endpoints

This module provides comprehensive API endpoints for managing the enhanced audit system:
- Audit queue monitoring and management
- Configuration snapshot management
- CDC log access and filtering
- Audit processor control and monitoring
- Audit health and statistics
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.core.database import get_db
from app.api.dependencies import get_current_admin
from app.models.auth.base import Administrator
from app.models.audit import AuditQueue, ConfigurationSnapshot, CDCLog, AuditProcessingStatus
from app.core.audit import AuditLog
from app.services.audit_processor import audit_processor_manager, get_audit_processing_health
from app.core.audit_mixins import ConfigurationVersioning, ChangeDataCapture
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas for audit management

class AuditQueueResponse(BaseModel):
    id: int
    table_name: str
    record_id: str
    operation: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None
    retry_count: int

    class Config:
        from_attributes = True


class ConfigurationSnapshotResponse(BaseModel):
    id: int
    config_type: str
    config_key: str
    snapshot_data: Dict[str, Any]
    version: int
    created_at: datetime
    created_by_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class CDCLogResponse(BaseModel):
    id: int
    table_name: str
    record_id: str
    operation: str
    change_data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    transaction_id: Optional[str] = None
    source: str

    class Config:
        from_attributes = True


class AuditProcessingStatusResponse(BaseModel):
    id: int
    processor_name: str
    last_processed_id: Optional[int] = None
    last_processed_at: Optional[datetime] = None
    status: str
    error_count: int
    last_error: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditHealthResponse(BaseModel):
    health_score: int
    health_status: str
    queue_stats: Dict[str, int]
    processor_stats: Dict[str, int]
    recommendations: List[str]


class ConfigurationSnapshotCreate(BaseModel):
    config_type: str = Field(..., max_length=50)
    config_key: str = Field(..., max_length=100)
    snapshot_data: Dict[str, Any]
    description: Optional[str] = None


class ProcessorControlRequest(BaseModel):
    action: str = Field(..., pattern="^(start|stop|restart)$")
    batch_size: Optional[int] = Field(100, ge=10, le=1000)


# Audit Queue Management Endpoints

@router.get("/queue", response_model=List[AuditQueueResponse])
async def get_audit_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    table_name: Optional[str] = Query(None),
    operation: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get audit queue entries with filtering and pagination."""
    try:
        query = db.query(AuditQueue)
        
        # Apply filters
        if status:
            query = query.filter(AuditQueue.status == status)
        if table_name:
            query = query.filter(AuditQueue.table_name == table_name)
        if operation:
            query = query.filter(AuditQueue.operation == operation)
        
        # Order by creation time (newest first)
        query = query.order_by(desc(AuditQueue.created_at))
        
        # Apply pagination
        entries = query.offset(skip).limit(limit).all()
        
        return entries
        
    except Exception as e:
        logger.error(f"Failed to get audit queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit queue")


@router.get("/queue/stats")
async def get_audit_queue_stats(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get audit queue statistics."""
    try:
        stats = {
            'pending': db.query(AuditQueue).filter_by(status='pending').count(),
            'processing': db.query(AuditQueue).filter_by(status='processing').count(),
            'completed': db.query(AuditQueue).filter_by(status='completed').count(),
            'failed': db.query(AuditQueue).filter_by(status='failed').count(),
            'total': db.query(AuditQueue).count()
        }
        
        # Add processing rates
        if stats['total'] > 0:
            stats['completion_rate'] = round((stats['completed'] / stats['total']) * 100, 2)
            stats['failure_rate'] = round((stats['failed'] / stats['total']) * 100, 2)
        else:
            stats['completion_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        # Add recent activity
        last_hour = datetime.now(timezone.utc) - timedelta(hours=1)
        stats['recent_activity'] = {
            'last_hour': db.query(AuditQueue).filter(AuditQueue.created_at >= last_hour).count(),
            'last_day': db.query(AuditQueue).filter(AuditQueue.created_at >= datetime.now(timezone.utc) - timedelta(days=1)).count()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get audit queue stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit queue statistics")


@router.post("/queue/{entry_id}/retry")
async def retry_audit_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Retry a failed audit entry."""
    try:
        entry = db.query(AuditQueue).filter_by(id=entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Audit entry not found")
        
        if entry.status != 'failed':
            raise HTTPException(status_code=400, detail="Only failed entries can be retried")
        
        if not entry.can_retry():
            raise HTTPException(status_code=400, detail="Entry has exceeded maximum retry attempts")
        
        # Reset entry for retry
        entry.status = 'pending'
        entry.error_message = None
        entry.processed_at = None
        
        db.commit()
        
        return {"message": "Audit entry queued for retry", "entry_id": entry_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry audit entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry audit entry")


# Configuration Snapshot Management

@router.get("/configuration-snapshots", response_model=List[ConfigurationSnapshotResponse])
async def get_configuration_snapshots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    config_type: Optional[str] = Query(None),
    config_key: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get configuration snapshots with filtering and pagination."""
    try:
        query = db.query(ConfigurationSnapshot)
        
        # Apply filters
        if config_type:
            query = query.filter(ConfigurationSnapshot.config_type == config_type)
        if config_key:
            query = query.filter(ConfigurationSnapshot.config_key == config_key)
        if is_active is not None:
            query = query.filter(ConfigurationSnapshot.is_active == is_active)
        
        # Order by version (newest first)
        query = query.order_by(desc(ConfigurationSnapshot.version))
        
        # Apply pagination
        snapshots = query.offset(skip).limit(limit).all()
        
        return snapshots
        
    except Exception as e:
        logger.error(f"Failed to get configuration snapshots: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration snapshots")


@router.post("/configuration-snapshots", response_model=ConfigurationSnapshotResponse)
async def create_configuration_snapshot(
    snapshot_data: ConfigurationSnapshotCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new configuration snapshot."""
    try:
        version = ConfigurationVersioning.create_snapshot(
            session=db,
            config_type=snapshot_data.config_type,
            config_key=snapshot_data.config_key,
            config_data=snapshot_data.snapshot_data,
            created_by_id=current_admin.id,
            description=snapshot_data.description
        )
        
        db.commit()
        
        # Return the created snapshot
        snapshot = db.query(ConfigurationSnapshot)\
            .filter_by(
                config_type=snapshot_data.config_type,
                config_key=snapshot_data.config_key,
                version=version
            ).first()
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Failed to create configuration snapshot: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create configuration snapshot")


@router.get("/configuration-snapshots/{snapshot_id}/activate")
async def activate_configuration_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Activate a specific configuration snapshot."""
    try:
        snapshot = db.query(ConfigurationSnapshot).filter_by(id=snapshot_id).first()
        if not snapshot:
            raise HTTPException(status_code=404, detail="Configuration snapshot not found")
        
        # Deactivate other snapshots for this config
        db.query(ConfigurationSnapshot)\
            .filter_by(config_type=snapshot.config_type, config_key=snapshot.config_key)\
            .update({'is_active': False})
        
        # Activate this snapshot
        snapshot.is_active = True
        
        db.commit()
        
        return {"message": "Configuration snapshot activated", "snapshot_id": snapshot_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate configuration snapshot {snapshot_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to activate configuration snapshot")


# CDC Log Access

@router.get("/cdc-log", response_model=List[CDCLogResponse])
async def get_cdc_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    table_name: Optional[str] = Query(None),
    operation: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),  # Last 24 hours by default, max 1 week
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get CDC log entries with filtering and pagination."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = db.query(CDCLog).filter(CDCLog.timestamp >= cutoff_time)
        
        # Apply filters
        if table_name:
            query = query.filter(CDCLog.table_name == table_name)
        if operation:
            query = query.filter(CDCLog.operation == operation)
        
        # Order by timestamp (newest first)
        query = query.order_by(desc(CDCLog.timestamp))
        
        # Apply pagination
        entries = query.offset(skip).limit(limit).all()
        
        return entries
        
    except Exception as e:
        logger.error(f"Failed to get CDC log: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve CDC log")


@router.get("/cdc-log/stats")
async def get_cdc_log_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get CDC log statistics."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get operation counts
        operation_stats = db.query(
            CDCLog.operation,
            func.count(CDCLog.id).label('count')
        ).filter(CDCLog.timestamp >= cutoff_time)\
         .group_by(CDCLog.operation)\
         .all()
        
        # Get table activity
        table_stats = db.query(
            CDCLog.table_name,
            func.count(CDCLog.id).label('count')
        ).filter(CDCLog.timestamp >= cutoff_time)\
         .group_by(CDCLog.table_name)\
         .order_by(desc(func.count(CDCLog.id)))\
         .limit(10)\
         .all()
        
        total_changes = db.query(CDCLog).filter(CDCLog.timestamp >= cutoff_time).count()
        
        return {
            'total_changes': total_changes,
            'time_period_hours': hours,
            'operation_breakdown': {op: count for op, count in operation_stats},
            'top_tables': [{'table_name': table, 'change_count': count} for table, count in table_stats]
        }
        
    except Exception as e:
        logger.error(f"Failed to get CDC log stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve CDC log statistics")


# Audit Processor Management

@router.get("/processors", response_model=List[AuditProcessingStatusResponse])
async def get_audit_processors(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get all audit processor statuses."""
    try:
        processors = db.query(AuditProcessingStatus).all()
        return processors
        
    except Exception as e:
        logger.error(f"Failed to get audit processors: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit processors")


@router.post("/processors/{processor_name}/control")
async def control_audit_processor(
    processor_name: str,
    control_request: ProcessorControlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Control audit processor (start/stop/restart)."""
    try:
        if control_request.action == "start":
            background_tasks.add_task(
                audit_processor_manager.start_processor,
                processor_name,
                control_request.batch_size
            )
            message = f"Audit processor {processor_name} start requested"
            
        elif control_request.action == "stop":
            background_tasks.add_task(
                audit_processor_manager.stop_processor,
                processor_name
            )
            message = f"Audit processor {processor_name} stop requested"
            
        elif control_request.action == "restart":
            background_tasks.add_task(
                audit_processor_manager.stop_processor,
                processor_name
            )
            background_tasks.add_task(
                audit_processor_manager.start_processor,
                processor_name,
                control_request.batch_size
            )
            message = f"Audit processor {processor_name} restart requested"
        
        return {"message": message, "processor_name": processor_name, "action": control_request.action}
        
    except Exception as e:
        logger.error(f"Failed to control audit processor {processor_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to control audit processor")


@router.get("/processors/stats")
async def get_processor_stats(
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get comprehensive processor statistics."""
    try:
        stats = audit_processor_manager.get_processor_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get processor stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve processor statistics")


# Audit Health and Monitoring

@router.get("/health", response_model=AuditHealthResponse, include_in_schema=False)
async def get_audit_health(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get comprehensive audit system health status."""
    try:
        health_data = get_audit_processing_health(db)
        return health_data
        
    except Exception as e:
        logger.error(f"Failed to get audit health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit health status")


@router.post("/maintenance/retry-failed")
async def retry_failed_entries(
    max_retries: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Retry all failed audit entries that can be retried."""
    try:
        retry_count = await audit_processor_manager.retry_failed_entries(db, max_retries)
        return {"message": f"Queued {retry_count} failed entries for retry", "retry_count": retry_count}
        
    except Exception as e:
        logger.error(f"Failed to retry failed entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry failed entries")


@router.post("/maintenance/cleanup")
async def cleanup_old_entries(
    days_to_keep: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Clean up old completed audit entries."""
    try:
        deleted_count = await audit_processor_manager.cleanup_old_entries(db, days_to_keep)
        return {"message": f"Cleaned up {deleted_count} old audit entries", "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Failed to cleanup old entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old entries")


@router.get("/dashboard")
async def get_audit_dashboard(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get comprehensive audit dashboard data."""
    try:
        # Get health status
        health_data = get_audit_processing_health(db)
        
        # Get queue stats
        queue_stats = {
            'pending': db.query(AuditQueue).filter_by(status='pending').count(),
            'processing': db.query(AuditQueue).filter_by(status='processing').count(),
            'completed': db.query(AuditQueue).filter_by(status='completed').count(),
            'failed': db.query(AuditQueue).filter_by(status='failed').count()
        }
        
        # Get processor stats
        processor_stats = audit_processor_manager.get_processor_stats()
        
        # Get recent activity (last 24 hours)
        last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_activity = {
            'audit_entries': db.query(AuditQueue).filter(AuditQueue.created_at >= last_24h).count(),
            'cdc_entries': db.query(CDCLog).filter(CDCLog.timestamp >= last_24h).count(),
            'config_snapshots': db.query(ConfigurationSnapshot).filter(ConfigurationSnapshot.created_at >= last_24h).count()
        }
        
        # Get top active tables
        top_tables = db.query(
            CDCLog.table_name,
            func.count(CDCLog.id).label('count')
        ).filter(CDCLog.timestamp >= last_24h)\
         .group_by(CDCLog.table_name)\
         .order_by(desc(func.count(CDCLog.id)))\
         .limit(5)\
         .all()
        
        return {
            'health': health_data,
            'queue_stats': queue_stats,
            'processor_stats': processor_stats,
            'recent_activity': recent_activity,
            'top_active_tables': [{'table_name': table, 'change_count': count} for table, count in top_tables],
            'timestamp': datetime.now(timezone.utc)
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit dashboard data")
