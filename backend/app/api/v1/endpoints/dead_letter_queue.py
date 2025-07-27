"""
Dead Letter Queue Management API Endpoints.

Provides API endpoints for managing failed background tasks and retry operations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.dependencies import get_current_admin_user
from app.models.auth.base import Administrator
from app.models.foundation import DeadLetterQueue, TaskExecutionLog
from app.tasks.maintenance_tasks import retry_dead_letter_task, get_dead_letter_stats
from app.core.celery import get_task_status, revoke_task, get_active_tasks
import structlog

logger = structlog.get_logger("isp.api.dead_letter_queue")

router = APIRouter()


# Pydantic schemas
class DeadLetterQueueResponse(BaseModel):
    """Response schema for dead letter queue items."""
    id: int
    task_id: str
    task_name: str
    queue_name: str
    exception_type: Optional[str]
    exception_message: Optional[str]
    retry_count: int
    failed_at: datetime
    status: str
    created_at: datetime
    processed_at: Optional[datetime]
    requeued_at: Optional[datetime]
    priority: int
    notes: Optional[str]

    class Config:
        from_attributes = True


class TaskExecutionLogResponse(BaseModel):
    """Response schema for task execution logs."""
    id: int
    task_id: str
    task_name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration_seconds: Optional[float]
    result: Optional[str]
    error: Optional[str]
    worker_name: Optional[str]
    queue_name: Optional[str]
    retry_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DeadLetterQueueStatsResponse(BaseModel):
    """Response schema for dead letter queue statistics."""
    pending_count: int
    requeued_count: int
    failed_count: int
    processed_count: int
    error_count: int
    failed_by_task: Dict[str, int]
    recent_failures_24h: int
    timestamp: str


class TaskStatusResponse(BaseModel):
    """Response schema for task status."""
    task_id: str
    status: str
    result: Optional[Any]
    traceback: Optional[str]
    date_done: Optional[datetime]
    successful: bool
    failed: bool
    ready: bool
    info: Optional[Any]


class RetryTaskRequest(BaseModel):
    """Request schema for retrying dead letter tasks."""
    notes: Optional[str] = Field(None, description="Optional notes for the retry attempt")


class PaginatedDeadLetterResponse(BaseModel):
    """Paginated response for dead letter queue items."""
    items: List[DeadLetterQueueResponse]
    total: int
    page: int
    size: int
    pages: int


class PaginatedTaskLogResponse(BaseModel):
    """Paginated response for task execution logs."""
    items: List[TaskExecutionLogResponse]
    total: int
    page: int
    size: int
    pages: int


@router.get("/stats", response_model=DeadLetterQueueStatsResponse)
async def get_dead_letter_queue_stats(
    current_admin: Administrator = Depends(get_current_admin_user)
) -> DeadLetterQueueStatsResponse:
    """Get statistics about the dead letter queue."""
    try:
        # Get stats using Celery task
        stats_result = get_dead_letter_stats.delay()
        stats = stats_result.get(timeout=30)
        
        return DeadLetterQueueStatsResponse(**stats)
        
    except Exception as e:
        logger.error("Failed to get dead letter queue stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dead letter queue statistics")


@router.get("/items", response_model=PaginatedDeadLetterResponse)
async def list_dead_letter_queue_items(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    task_name: Optional[str] = Query(None, description="Filter by task name"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> PaginatedDeadLetterResponse:
    """List dead letter queue items with pagination and filtering."""
    try:
        # Build query
        query = db.query(DeadLetterQueue)
        
        # Apply filters
        if status:
            query = query.filter(DeadLetterQueue.status == status)
        if task_name:
            query = query.filter(DeadLetterQueue.task_name.ilike(f"%{task_name}%"))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        items = query.order_by(DeadLetterQueue.created_at.desc()).offset(offset).limit(size).all()
        
        # Calculate pages
        pages = (total + size - 1) // size
        
        return PaginatedDeadLetterResponse(
            items=[DeadLetterQueueResponse.from_orm(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error("Failed to list dead letter queue items", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dead letter queue items")


@router.get("/items/{dlq_id}", response_model=DeadLetterQueueResponse)
async def get_dead_letter_queue_item(
    dlq_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> DeadLetterQueueResponse:
    """Get a specific dead letter queue item."""
    try:
        item = db.query(DeadLetterQueue).filter(DeadLetterQueue.id == dlq_id).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Dead letter queue item not found")
        
        return DeadLetterQueueResponse.from_orm(item)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get dead letter queue item", dlq_id=dlq_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dead letter queue item")


@router.post("/items/{dlq_id}/retry")
async def retry_dead_letter_queue_item(
    dlq_id: int,
    request: RetryTaskRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Manually retry a specific dead letter queue item."""
    try:
        # Check if item exists and is retryable
        item = db.query(DeadLetterQueue).filter(
            DeadLetterQueue.id == dlq_id,
            DeadLetterQueue.status.in_(['pending', 'failed'])
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=404, 
                detail="Dead letter queue item not found or not retryable"
            )
        
        # Update notes if provided
        if request.notes:
            item.notes = request.notes
            db.commit()
        
        # Queue the retry task
        retry_result = retry_dead_letter_task.delay(dlq_id)
        
        logger.info(
            "Dead letter queue item retry initiated",
            dlq_id=dlq_id,
            task_id=item.task_id,
            task_name=item.task_name,
            retry_task_id=retry_result.id,
            admin_id=current_admin.id
        )
        
        return {
            "success": True,
            "message": "Retry initiated",
            "dlq_id": dlq_id,
            "retry_task_id": retry_result.id,
            "task_id": item.task_id,
            "task_name": item.task_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retry dead letter queue item", dlq_id=dlq_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retry dead letter queue item")


@router.delete("/items/{dlq_id}")
async def delete_dead_letter_queue_item(
    dlq_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Delete a dead letter queue item (mark as processed)."""
    try:
        item = db.query(DeadLetterQueue).filter(DeadLetterQueue.id == dlq_id).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Dead letter queue item not found")
        
        # Mark as processed instead of deleting
        item.status = 'processed'
        item.processed_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(
            "Dead letter queue item marked as processed",
            dlq_id=dlq_id,
            task_id=item.task_id,
            task_name=item.task_name,
            admin_id=current_admin.id
        )
        
        return {
            "success": True,
            "message": "Dead letter queue item marked as processed",
            "dlq_id": dlq_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete dead letter queue item", dlq_id=dlq_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete dead letter queue item")


@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status_endpoint(
    task_id: str,
    current_admin: Administrator = Depends(get_current_admin_user)
) -> TaskStatusResponse:
    """Get the status of a specific task."""
    try:
        status_info = get_task_status(task_id)
        return TaskStatusResponse(**status_info)
        
    except Exception as e:
        logger.error("Failed to get task status", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve task status")


@router.post("/{task_id}/revoke")
async def revoke_task_endpoint(
    task_id: str,
    terminate: bool = Query(False, description="Whether to terminate the task"),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Revoke a running task."""
    try:
        success = revoke_task(task_id, terminate=terminate)
        
        if success:
            logger.info(
                "Task revoked",
                task_id=task_id,
                terminate=terminate,
                admin_id=current_admin.id
            )
            return {
                "success": True,
                "message": "Task revoked successfully",
                "task_id": task_id,
                "terminated": terminate
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to revoke task")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to revoke task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to revoke task")


@router.get("/active")
async def get_active_tasks_endpoint(
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get all active tasks across workers."""
    try:
        active_tasks = get_active_tasks()
        return {
            "success": True,
            "data": active_tasks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get active tasks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve active tasks")


@router.get("/logs", response_model=PaginatedTaskLogResponse)
async def list_task_execution_logs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    task_name: Optional[str] = Query(None, description="Filter by task name"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> PaginatedTaskLogResponse:
    """List task execution logs with pagination and filtering."""
    try:
        # Build query with time filter
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = db.query(TaskExecutionLog).filter(TaskExecutionLog.created_at >= cutoff_time)
        
        # Apply filters
        if status:
            query = query.filter(TaskExecutionLog.status == status)
        if task_name:
            query = query.filter(TaskExecutionLog.task_name.ilike(f"%{task_name}%"))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        items = query.order_by(TaskExecutionLog.created_at.desc()).offset(offset).limit(size).all()
        
        # Calculate pages
        pages = (total + size - 1) // size
        
        return PaginatedTaskLogResponse(
            items=[TaskExecutionLogResponse.from_orm(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error("Failed to list task execution logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve task execution logs")


@router.get("/dashboard")
async def get_dead_letter_dashboard(
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get comprehensive dashboard data for dead letter queue monitoring."""
    try:
        # Get stats
        stats_result = get_dead_letter_stats.delay()
        stats = stats_result.get(timeout=30)
        
        # Get active tasks
        active_tasks = get_active_tasks()
        
        # Calculate health metrics
        total_failed = stats.get('failed_count', 0) + stats.get('error_count', 0)
        total_processed = stats.get('processed_count', 0) + stats.get('requeued_count', 0)
        success_rate = (total_processed / (total_processed + total_failed)) * 100 if (total_processed + total_failed) > 0 else 100
        
        return {
            "success": True,
            "data": {
                "stats": stats,
                "active_tasks": active_tasks,
                "health_metrics": {
                    "success_rate": round(success_rate, 2),
                    "total_failed": total_failed,
                    "total_processed": total_processed,
                    "recent_failures": stats.get('recent_failures_24h', 0)
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get dead letter dashboard", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")



# ============================================================================
# Clean RESTful API - No Backward Compatibility Needed (Pre-Production)
# ============================================================================

