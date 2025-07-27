"""
Celery Configuration and Dead-Letter Queue for ISP Framework.

Provides background task processing with comprehensive error handling and retry logic.
"""
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from celery import Celery, Task
from celery.signals import task_failure, task_retry, task_success
import structlog

from app.core.config import settings


# Configure Celery app
celery_app = Celery(
    "isp_framework",
    broker=getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
    backend=getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
    include=[
        'app.tasks.service_provisioning',
        'app.tasks.billing_tasks',
        'app.tasks.network_tasks',
        'app.tasks.customer_notifications',
        'app.tasks.monitoring_tasks',
        'app.tasks.maintenance_tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'app.tasks.service_provisioning.*': {'queue': 'service_provisioning'},
        'app.tasks.billing_tasks.*': {'queue': 'billing'},
        'app.tasks.network_tasks.*': {'queue': 'network'},
        'app.tasks.customer_notifications.*': {'queue': 'notifications'},
        'app.tasks.monitoring_tasks.*': {'queue': 'monitoring'},
        'app.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
    },
    
    # Task execution
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task retry and dead letter queue configuration
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Dead letter queue settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-failed-tasks': {
            'task': 'app.tasks.maintenance_tasks.cleanup_failed_tasks',
            'schedule': 300.0,  # Every 5 minutes
        },
        'process-dead-letter-queue': {
            'task': 'app.tasks.maintenance_tasks.process_dead_letter_queue',
            'schedule': 600.0,  # Every 10 minutes
        },
        'billing-cycle-processing': {
            'task': 'app.tasks.billing_tasks.process_billing_cycle',
            'schedule': 3600.0,  # Every hour
        },
        'network-monitoring': {
            'task': 'app.tasks.monitoring_tasks.monitor_network_devices',
            'schedule': 180.0,  # Every 3 minutes
        },
        'customer-usage-tracking': {
            'task': 'app.tasks.monitoring_tasks.update_customer_usage',
            'schedule': 900.0,  # Every 15 minutes
        },
    },
)

# Logger for Celery tasks
logger = structlog.get_logger("isp.celery")


class ISPFrameworkTask(Task):
    """Base task class with enhanced error handling and dead-letter queue support."""
    
    def __init__(self):
        self.logger = structlog.get_logger(f"isp.celery.{self.name}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure with comprehensive logging and alerting."""
        self.logger.error(
            "Task failed",
            task_id=task_id,
            task_name=self.name,
            exception=str(exc),
            args=args,
            kwargs=kwargs,
            traceback=str(einfo)
        )
        
        # Send to dead letter queue if max retries exceeded
        if self.request.retries >= self.max_retries:
            self._send_to_dead_letter_queue(task_id, exc, args, kwargs, einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry with logging."""
        self.logger.warning(
            "Task retry",
            task_id=task_id,
            task_name=self.name,
            retry_count=self.request.retries,
            max_retries=self.max_retries,
            exception=str(exc),
            next_retry=datetime.now(timezone.utc) + timedelta(seconds=self.default_retry_delay)
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful task completion."""
        self.logger.info(
            "Task completed successfully",
            task_id=task_id,
            task_name=self.name,
            result_type=type(retval).__name__,
            execution_time=getattr(self.request, 'execution_time', None)
        )
    
    def _send_to_dead_letter_queue(self, task_id, exc, args, kwargs, einfo):
        """Send failed task to dead letter queue for manual processing."""
        try:
            from app.tasks.maintenance_tasks import add_to_dead_letter_queue
            
            dead_letter_data = {
                'task_id': task_id,
                'task_name': self.name,
                'args': args,
                'kwargs': kwargs,
                'exception': str(exc),
                'traceback': str(einfo),
                'failed_at': datetime.now(timezone.utc).isoformat(),
                'retry_count': self.request.retries,
                'queue': getattr(self.request, 'delivery_info', {}).get('routing_key', 'default')
            }
            
            # Add to dead letter queue asynchronously
            add_to_dead_letter_queue.delay(dead_letter_data)
            
            self.logger.critical(
                "Task sent to dead letter queue",
                task_id=task_id,
                task_name=self.name,
                retry_count=self.request.retries
            )
            
            # Trigger alert for critical task failure
            self._trigger_task_failure_alert(task_id, exc, args, kwargs)
            
        except Exception as dlq_error:
            self.logger.error(
                "Failed to send task to dead letter queue",
                task_id=task_id,
                task_name=self.name,
                dlq_error=str(dlq_error)
            )
    
    def _trigger_task_failure_alert(self, task_id, exc, args, kwargs):
        """Trigger alert for critical task failure."""
        try:
            from app.core.error_handling import ISPException, ErrorSeverity, ErrorCategory, ErrorImpact
            from app.core.alerting import grafana_alert_manager
            import asyncio
            
            # Create error detail for task failure
            error_detail = ISPException(
                title=f"Critical Task Failure: {self.name}",
                detail=f"Task {task_id} failed after {self.max_retries} retries: {str(exc)}",
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
                impact=ErrorImpact.OPERATIONAL,
                context={
                    'task_id': task_id,
                    'task_name': self.name,
                    'retry_count': self.request.retries,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
            )
            
            # Process alert (run in event loop if available)
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(grafana_alert_manager.process_error(error_detail))
            except RuntimeError:
                # No event loop, create new one
                asyncio.run(grafana_alert_manager.process_error(error_detail))
                
        except Exception as alert_error:
            self.logger.error(
                "Failed to trigger task failure alert",
                task_id=task_id,
                alert_error=str(alert_error)
            )


# Set the base task class
celery_app.Task = ISPFrameworkTask


# Celery signal handlers
@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Global task failure handler."""
    logger.error(
        "Global task failure handler",
        task_id=task_id,
        task_name=sender.name if sender else "unknown",
        exception=str(exception),
        sender=str(sender)
    )


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwargs):
    """Global task retry handler."""
    logger.warning(
        "Global task retry handler",
        task_id=task_id,
        task_name=sender.name if sender else "unknown",
        reason=str(reason),
        sender=str(sender)
    )


@task_success.connect
def task_success_handler(sender=None, task_id=None, result=None, **kwargs):
    """Global task success handler."""
    logger.info(
        "Global task success handler",
        task_id=task_id,
        task_name=sender.name if sender else "unknown",
        result_type=type(result).__name__ if result else "None",
        sender=str(sender)
    )


# Utility functions for task management
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get comprehensive task status information."""
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result,
            'traceback': result.traceback,
            'date_done': result.date_done,
            'successful': result.successful(),
            'failed': result.failed(),
            'ready': result.ready(),
            'info': result.info
        }
    except Exception as e:
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        }


def revoke_task(task_id: str, terminate: bool = False) -> bool:
    """Revoke a running task."""
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        logger.info(
            "Task revoked",
            task_id=task_id,
            terminate=terminate
        )
        return True
    except Exception as e:
        logger.error(
            "Failed to revoke task",
            task_id=task_id,
            error=str(e)
        )
        return False


def get_active_tasks() -> Dict[str, Any]:
    """Get all active tasks across workers."""
    try:
        inspect = celery_app.control.inspect()
        return {
            'active': inspect.active(),
            'scheduled': inspect.scheduled(),
            'reserved': inspect.reserved(),
            'stats': inspect.stats()
        }
    except Exception as e:
        logger.error("Failed to get active tasks", error=str(e))
        return {}


def purge_queue(queue_name: str) -> int:
    """Purge all messages from a specific queue."""
    try:
        purged_count = celery_app.control.purge()
        logger.info(
            "Queue purged",
            queue_name=queue_name,
            purged_count=purged_count
        )
        return purged_count
    except Exception as e:
        logger.error(
            "Failed to purge queue",
            queue_name=queue_name,
            error=str(e)
        )
        return 0


# Export the Celery app
__all__ = ['celery_app', 'ISPFrameworkTask', 'get_task_status', 'revoke_task', 'get_active_tasks', 'purge_queue']
