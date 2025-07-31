"""
Maintenance Tasks for ISP Framework.

Handles dead-letter queue processing, cleanup, and system maintenance tasks.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import structlog
from celery import current_app

from app.core.celery import ISPFrameworkTask, celery_app
from app.core.database import get_db
from app.models.foundation import DeadLetterQueue, TaskExecutionLog

logger = structlog.get_logger("isp.tasks.maintenance")


@celery_app.task(
    bind=True,
    base=ISPFrameworkTask,
    name="app.tasks.maintenance_tasks.add_to_dead_letter_queue",
)
def add_to_dead_letter_queue(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a failed task to the dead letter queue for manual processing."""
    try:
        db = next(get_db())

        # Create dead letter queue entry
        dlq_entry = DeadLetterQueue(
            task_id=task_data["task_id"],
            task_name=task_data["task_name"],
            queue_name=task_data.get("queue", "default"),
            task_args=json.dumps(task_data.get("args", [])),
            task_kwargs=json.dumps(task_data.get("kwargs", {})),
            exception_type=type(task_data.get("exception", "")).__name__,
            exception_message=str(task_data.get("exception", "")),
            traceback=task_data.get("traceback", ""),
            retry_count=task_data.get("retry_count", 0),
            failed_at=datetime.fromisoformat(task_data["failed_at"]),
            status="pending",
            created_at=datetime.now(timezone.utc),
        )

        db.add(dlq_entry)
        db.commit()

        logger.info(
            "Task added to dead letter queue",
            task_id=task_data["task_id"],
            task_name=task_data["task_name"],
            dlq_id=dlq_entry.id,
        )

        return {
            "success": True,
            "dlq_id": dlq_entry.id,
            "task_id": task_data["task_id"],
        }

    except Exception as e:
        logger.error(
            "Failed to add task to dead letter queue",
            task_id=task_data.get("task_id"),
            error=str(e),
        )
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=ISPFrameworkTask,
    name="app.tasks.maintenance_tasks.process_dead_letter_queue",
)
def process_dead_letter_queue(self) -> Dict[str, Any]:
    """Process pending items in the dead letter queue."""
    try:
        db = next(get_db())

        # Get pending dead letter queue items
        pending_items = (
            db.query(DeadLetterQueue)
            .filter(
                DeadLetterQueue.status == "pending",
                DeadLetterQueue.created_at
                < datetime.now(timezone.utc)
                - timedelta(minutes=10),  # Wait 10 minutes before processing
            )
            .limit(50)
            .all()
        )

        processed_count = 0
        requeued_count = 0
        failed_count = 0

        for item in pending_items:
            try:
                # Attempt to requeue the task if it's retryable
                if item.retry_count < 5 and item.task_name in _get_retryable_tasks():
                    success = _retry_dead_letter_task(item)
                    if success:
                        item.status = "requeued"
                        item.requeued_at = datetime.now(timezone.utc)
                        item.retry_count += 1
                        requeued_count += 1
                    else:
                        item.status = "failed"
                        item.processed_at = datetime.now(timezone.utc)
                        failed_count += 1
                else:
                    # Mark as failed if not retryable or max retries exceeded
                    item.status = "failed"
                    item.processed_at = datetime.now(timezone.utc)
                    failed_count += 1

                processed_count += 1

            except Exception as e:
                logger.error(
                    "Error processing dead letter queue item",
                    dlq_id=item.id,
                    task_id=item.task_id,
                    error=str(e),
                )
                item.status = "error"
                item.processed_at = datetime.now(timezone.utc)
                failed_count += 1

        db.commit()

        result = {
            "processed_count": processed_count,
            "requeued_count": requeued_count,
            "failed_count": failed_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("Dead letter queue processing completed", **result)

        return result

    except Exception as e:
        logger.error("Dead letter queue processing failed", error=str(e))
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=ISPFrameworkTask,
    name="app.tasks.maintenance_tasks.cleanup_failed_tasks",
)
def cleanup_failed_tasks(self) -> Dict[str, Any]:
    """Clean up old failed tasks and logs."""
    try:
        db = next(get_db())

        # Clean up old dead letter queue entries (older than 30 days)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        old_dlq_count = (
            db.query(DeadLetterQueue)
            .filter(
                DeadLetterQueue.created_at < cutoff_date,
                DeadLetterQueue.status.in_(["failed", "processed", "requeued"]),
            )
            .count()
        )

        db.query(DeadLetterQueue).filter(
            DeadLetterQueue.created_at < cutoff_date,
            DeadLetterQueue.status.in_(["failed", "processed", "requeued"]),
        ).delete()

        # Clean up old task execution logs (older than 7 days)
        log_cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

        old_log_count = (
            db.query(TaskExecutionLog)
            .filter(TaskExecutionLog.created_at < log_cutoff_date)
            .count()
        )

        db.query(TaskExecutionLog).filter(
            TaskExecutionLog.created_at < log_cutoff_date
        ).delete()

        db.commit()

        result = {
            "cleaned_dlq_entries": old_dlq_count,
            "cleaned_log_entries": old_log_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("Task cleanup completed", **result)

        return result

    except Exception as e:
        logger.error("Task cleanup failed", error=str(e))
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=ISPFrameworkTask,
    name="app.tasks.maintenance_tasks.retry_dead_letter_task",
)
def retry_dead_letter_task(self, dlq_id: int) -> Dict[str, Any]:
    """Manually retry a specific dead letter queue task."""
    try:
        db = next(get_db())

        # Get the dead letter queue item
        dlq_item = (
            db.query(DeadLetterQueue)
            .filter(
                DeadLetterQueue.id == dlq_id,
                DeadLetterQueue.status.in_(["pending", "failed"]),
            )
            .first()
        )

        if not dlq_item:
            raise ValueError(
                f"Dead letter queue item {dlq_id} not found or not retryable"
            )

        # Attempt to retry the task
        success = _retry_dead_letter_task(dlq_item)

        if success:
            dlq_item.status = "requeued"
            dlq_item.requeued_at = datetime.now(timezone.utc)
            dlq_item.retry_count += 1
            db.commit()

            logger.info(
                "Dead letter task manually retried",
                dlq_id=dlq_id,
                task_id=dlq_item.task_id,
                task_name=dlq_item.task_name,
            )

            return {
                "success": True,
                "dlq_id": dlq_id,
                "task_id": dlq_item.task_id,
                "retry_count": dlq_item.retry_count,
            }
        else:
            dlq_item.status = "retry_failed"
            dlq_item.processed_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "success": False,
                "dlq_id": dlq_id,
                "task_id": dlq_item.task_id,
                "error": "Failed to requeue task",
            }

    except Exception as e:
        logger.error(
            "Manual retry of dead letter task failed", dlq_id=dlq_id, error=str(e)
        )
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=ISPFrameworkTask,
    name="app.tasks.maintenance_tasks.get_dead_letter_stats",
)
def get_dead_letter_stats(self) -> Dict[str, Any]:
    """Get statistics about the dead letter queue."""
    try:
        db = next(get_db())

        # Get counts by status
        stats = {}
        for status in ["pending", "requeued", "failed", "processed", "error"]:
            count = (
                db.query(DeadLetterQueue)
                .filter(DeadLetterQueue.status == status)
                .count()
            )
            stats[f"{status}_count"] = count

        # Get counts by task name for failed tasks
        failed_by_task = (
            db.query(
                DeadLetterQueue.task_name,
                db.func.count(DeadLetterQueue.id).label("count"),
            )
            .filter(DeadLetterQueue.status == "failed")
            .group_by(DeadLetterQueue.task_name)
            .all()
        )

        stats["failed_by_task"] = {
            task_name: count for task_name, count in failed_by_task
        }

        # Get recent failures (last 24 hours)
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_failures = (
            db.query(DeadLetterQueue)
            .filter(
                DeadLetterQueue.failed_at >= recent_cutoff,
                DeadLetterQueue.status == "failed",
            )
            .count()
        )

        stats["recent_failures_24h"] = recent_failures
        stats["timestamp"] = datetime.now(timezone.utc).isoformat()

        return stats

    except Exception as e:
        logger.error("Failed to get dead letter stats", error=str(e))
        raise
    finally:
        db.close()


def _get_retryable_tasks() -> List[str]:
    """Get list of task names that are safe to retry."""
    return [
        "app.tasks.customer_notifications.send_email",
        "app.tasks.customer_notifications.send_sms",
        "app.tasks.billing_tasks.generate_invoice",
        "app.tasks.billing_tasks.process_payment",
        "app.tasks.monitoring_tasks.update_customer_usage",
        "app.tasks.network_tasks.sync_device_config",
        "app.tasks.service_provisioning.provision_internet_service",
        "app.tasks.service_provisioning.suspend_service",
        "app.tasks.service_provisioning.restore_service",
    ]


def _retry_dead_letter_task(dlq_item: DeadLetterQueue) -> bool:
    """Attempt to retry a dead letter queue task."""
    try:
        # Parse task arguments
        args = json.loads(dlq_item.task_args) if dlq_item.task_args else []
        kwargs = json.loads(dlq_item.task_kwargs) if dlq_item.task_kwargs else {}

        # Get the task by name
        task = current_app.tasks.get(dlq_item.task_name)
        if not task:
            logger.error(
                "Task not found for retry",
                task_name=dlq_item.task_name,
                dlq_id=dlq_item.id,
            )
            return False

        # Apply the task with modified retry settings
        task.apply_async(
            args=args,
            kwargs=kwargs,
            queue=dlq_item.queue_name,
            retry=True,
            retry_policy={
                "max_retries": 2,
                "interval_start": 60,
                "interval_step": 60,
                "interval_max": 300,
            },
        )

        logger.info(
            "Dead letter task requeued",
            task_name=dlq_item.task_name,
            task_id=dlq_item.task_id,
            dlq_id=dlq_item.id,
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to retry dead letter task",
            task_name=dlq_item.task_name,
            task_id=dlq_item.task_id,
            dlq_id=dlq_item.id,
            error=str(e),
        )
        return False


# Task execution logging decorator
def log_task_execution(func):
    """Decorator to log task execution details."""

    def wrapper(*args, **kwargs):
        task_id = getattr(func.request, "id", "unknown")
        task_name = func.name
        start_time = datetime.now(timezone.utc)

        try:
            result = func(*args, **kwargs)

            # Log successful execution
            _log_task_execution(
                task_id=task_id,
                task_name=task_name,
                status="success",
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                result=str(result)[:1000],  # Truncate long results
            )

            return result

        except Exception as e:
            # Log failed execution
            _log_task_execution(
                task_id=task_id,
                task_name=task_name,
                status="failed",
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                error=str(e)[:1000],  # Truncate long errors
            )
            raise

    return wrapper


def _log_task_execution(
    task_id: str,
    task_name: str,
    status: str,
    start_time: datetime,
    end_time: datetime,
    result: str = None,
    error: str = None,
):
    """Log task execution to database."""
    try:
        db = next(get_db())

        execution_log = TaskExecutionLog(
            task_id=task_id,
            task_name=task_name,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
            result=result,
            error=error,
            created_at=datetime.now(timezone.utc),
        )

        db.add(execution_log)
        db.commit()

    except Exception as e:
        logger.error(
            "Failed to log task execution",
            task_id=task_id,
            task_name=task_name,
            error=str(e),
        )
    finally:
        db.close()
