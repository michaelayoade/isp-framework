"""
Provisioning Queue Service

Service layer for async provisioning queue management including:
- Job creation and scheduling
- Retry logic and error handling
- Worker coordination and load balancing
- Status tracking and monitoring
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.schemas.provisioning_queue import (
    ProvisioningJobCreate, ProvisioningJobUpdate, ProvisioningJob,
    ProvisioningJobList, ProvisioningWorkerStatus
)
from app.core.exceptions import NotFoundError, ValidationError
from app.services.webhook_integration_service import WebhookTriggers
import logging
import uuid

logger = logging.getLogger(__name__)


class ProvisioningQueueService:
    """Service layer for provisioning queue management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
    
    def create_job(self, job_data: ProvisioningJobCreate, created_by: Optional[int] = None) -> ProvisioningJob:
        """Create a new provisioning job."""
        try:
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            
            # Calculate scheduled time based on priority
            scheduled_for = self._calculate_scheduled_time(job_data.priority, job_data.scheduled_for)
            
            # Create job record
            job_dict = job_data.model_dump()
            job_dict.update({
                "job_id": job_id,
                "scheduled_for": scheduled_for,
                "status": "queued",
                "created_by": created_by,
                "created_at": datetime.now(timezone.utc)
            })
            
            # Placeholder - implement when provisioning job repository is available
            # job = self.provisioning_job_repo.create(job_dict)
            
            # Mock implementation
            job = ProvisioningJob(
                id=1,  # Mock ID
                job_id=job_id,
                **job_dict
            )
            
            # Create initial history entry
            self._create_history_entry(job.id, None, "queued", "Job created and queued", created_by)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.provisioning_job_created({
                    'job_id': job_id,
                    'service_id': job_data.service_id,
                    'service_type': job_data.service_type,
                    'customer_id': job_data.customer_id,
                    'priority': job_data.priority,
                    'scheduled_for': scheduled_for.isoformat(),
                    'created_at': job.created_at.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger provisioning.job_created webhook: {e}")
            
            logger.info(f"Created provisioning job {job_id} for service {job_data.service_id}")
            return job
            
        except Exception as e:
            logger.error(f"Error creating provisioning job: {e}")
            raise
    
    def get_job(self, job_id: str) -> ProvisioningJob:
        """Get a provisioning job by ID."""
        # Placeholder - implement when provisioning job repository is available
        # job = self.provisioning_job_repo.get_by_job_id(job_id)
        # if not job:
        #     raise NotFoundError(f"Provisioning job with id {job_id} not found")
        # return job
        
        # Mock implementation
        if not job_id:
            raise NotFoundError(f"Provisioning job with id {job_id} not found")
        
        return ProvisioningJob(
            id=1,
            job_id=job_id,
            service_id=1,
            service_type="internet",
            customer_id=1,
            priority="normal",
            status="queued",
            scheduled_for=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
    
    def update_job_status(
        self, 
        job_id: str, 
        new_status: str, 
        message: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        updated_by: Optional[int] = None
    ) -> ProvisioningJob:
        """Update provisioning job status."""
        # Get existing job
        job = self.get_job(job_id)
        old_status = job.status
        
        try:
            # Update job fields
            update_dict = {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if new_status == "processing":
                update_dict["started_at"] = datetime.now(timezone.utc)
            elif new_status in ["completed", "failed", "cancelled"]:
                update_dict["completed_at"] = datetime.now(timezone.utc)
            
            if result_data:
                update_dict["result_data"] = result_data
            
            if error_message:
                update_dict["error_message"] = error_message
            
            # Handle retry logic for failed jobs
            if new_status == "failed":
                job.retry_count += 1
                if job.retry_count < job.max_retries:
                    # Schedule retry with exponential backoff
                    retry_delay = min(300 * (2 ** job.retry_count), 3600)  # Max 1 hour
                    update_dict["next_retry_at"] = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
                    update_dict["status"] = "queued"  # Reset to queued for retry
                    new_status = "queued"
            
            # Placeholder - implement when provisioning job repository is available
            # updated_job = self.provisioning_job_repo.update(job.id, update_dict)
            
            # Mock implementation
            for key, value in update_dict.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            # Create history entry
            self._create_history_entry(job.id, old_status, new_status, message, updated_by)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.provisioning_job_status_changed({
                    'job_id': job_id,
                    'service_id': job.service_id,
                    'service_type': job.service_type,
                    'customer_id': job.customer_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'message': message,
                    'updated_at': update_dict["updated_at"].isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger provisioning.job_status_changed webhook: {e}")
            
            logger.info(f"Updated provisioning job {job_id} status: {old_status} -> {new_status}")
            return job
            
        except Exception as e:
            logger.error(f"Error updating provisioning job {job_id}: {e}")
            raise
    
    def list_jobs(
        self, 
        page: int = 1, 
        per_page: int = 25,
        status: Optional[str] = None,
        service_type: Optional[str] = None,
        customer_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> ProvisioningJobList:
        """List provisioning jobs with pagination and filtering."""
        # Placeholder - implement when provisioning job repository is available
        # filters = {}
        # if status:
        #     filters["status"] = status
        # if service_type:
        #     filters["service_type"] = service_type
        # if customer_id:
        #     filters["customer_id"] = customer_id
        # if priority:
        #     filters["priority"] = priority
        
        # skip = (page - 1) * per_page
        # jobs = self.provisioning_job_repo.get_all(skip=skip, limit=per_page, filters=filters)
        # total = self.provisioning_job_repo.count(filters=filters)
        
        # Mock implementation
        jobs = [
            ProvisioningJob(
                id=1,
                job_id="job-123",
                service_id=1,
                service_type="internet",
                customer_id=1,
                priority="normal",
                status="queued",
                scheduled_for=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        total = len(jobs)
        pages = ((total - 1) // per_page) + 1 if total > 0 else 0
        
        return ProvisioningJobList(
            jobs=jobs,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
    
    def get_next_job(self, worker_id: str, supported_service_types: List[str]) -> Optional[ProvisioningJob]:
        """Get the next job for a worker to process."""
        # Placeholder - implement when provisioning job repository is available
        # Get highest priority job that is ready to run
        # filters = {
        #     "status": "queued",
        #     "scheduled_for__lte": datetime.now(timezone.utc),
        #     "service_type__in": supported_service_types
        # }
        # job = self.provisioning_job_repo.get_next_priority_job(filters)
        
        # Mock implementation
        return None  # No jobs available
    
    def cancel_job(self, job_id: str, reason: str, cancelled_by: Optional[int] = None) -> ProvisioningJob:
        """Cancel a provisioning job."""
        job = self.get_job(job_id)
        
        if job.status in ["completed", "cancelled"]:
            raise ValidationError(f"Cannot cancel job with status '{job.status}'")
        
        return self.update_job_status(
            job_id, 
            "cancelled", 
            f"Job cancelled: {reason}",
            updated_by=cancelled_by
        )
    
    def retry_job(self, job_id: str, retried_by: Optional[int] = None) -> ProvisioningJob:
        """Manually retry a failed provisioning job."""
        job = self.get_job(job_id)
        
        if job.status != "failed":
            raise ValidationError(f"Cannot retry job with status '{job.status}'")
        
        # Reset retry fields
        update_dict = {
            "status": "queued",
            "retry_count": 0,
            "next_retry_at": None,
            "error_message": None,
            "error_details": None,
            "scheduled_for": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Placeholder - implement when provisioning job repository is available
        # updated_job = self.provisioning_job_repo.update(job.id, update_dict)
        
        # Mock implementation
        for key, value in update_dict.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        self._create_history_entry(job.id, "failed", "queued", "Job manually retried", retried_by)
        
        logger.info(f"Manually retried provisioning job {job_id}")
        return job
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get provisioning queue statistics."""
        # Placeholder - implement when provisioning job repository is available
        # stats = self.provisioning_job_repo.get_statistics()
        
        # Mock implementation
        return {
            "total_jobs": 0,
            "queued_jobs": 0,
            "processing_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "cancelled_jobs": 0,
            "average_processing_time": 0,
            "success_rate": 100.0,
            "active_workers": 0
        }
    
    def _calculate_scheduled_time(self, priority: str, requested_time: Optional[datetime] = None) -> datetime:
        """Calculate when a job should be scheduled based on priority."""
        now = datetime.now(timezone.utc)
        
        if requested_time and requested_time > now:
            return requested_time
        
        # Priority-based scheduling delays
        delays = {
            "urgent": 0,      # Immediate
            "high": 30,       # 30 seconds
            "normal": 60,     # 1 minute
            "low": 300        # 5 minutes
        }
        
        delay = delays.get(priority, 60)
        return now + timedelta(seconds=delay)
    
    def _create_history_entry(
        self, 
        job_id: int, 
        old_status: Optional[str], 
        new_status: str, 
        message: Optional[str] = None,
        created_by: Optional[int] = None
    ):
        """Create a history entry for job status change."""
        # Placeholder - implement when provisioning job history repository is available
        # history_data = {
        #     "job_id": job_id,
        #     "old_status": old_status,
        #     "new_status": new_status,
        #     "message": message,
        #     "created_by": created_by,
        #     "created_at": datetime.now(timezone.utc)
        # }
        # self.provisioning_job_history_repo.create(history_data)
        
        logger.debug(f"Job {job_id} status change: {old_status} -> {new_status} ({message})")
