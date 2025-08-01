"""
Provisioning Job Repository

Repository layer for provisioning job management including:
- CRUD operations for provisioning jobs
- Queue management and job scheduling
- Status tracking and history management
- Worker assignment and load balancing
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import Session, joinedload

from app.models.provisioning_queue import (
    ProvisioningJob,
    ProvisioningJobHistory,
    ProvisioningWorkerStatus
)
from app.repositories.base import BaseRepository


class ProvisioningJobRepository(BaseRepository[ProvisioningJob]):
    """Repository for provisioning job management."""

    def __init__(self, db: Session):
        super().__init__(ProvisioningJob, db)

    def create_job(self, job_data: Dict[str, Any]) -> ProvisioningJob:
        """Create a new provisioning job."""
        job = ProvisioningJob(**job_data)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_by_job_id(self, job_id: str) -> Optional[ProvisioningJob]:
        """Get a provisioning job by job_id."""
        return self.db.query(ProvisioningJob).filter(
            ProvisioningJob.job_id == job_id
        ).first()

    def update_job_status(
        self,
        job_id: str,
        new_status: str,
        message: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[ProvisioningJob]:
        """Update job status and create history entry."""
        job = self.get_by_job_id(job_id)
        if not job:
            return None

        old_status = job.status
        job.status = new_status
        job.updated_at = datetime.now(timezone.utc)

        if message:
            job.status_message = message
        if result_data:
            job.result_data = result_data
        if error_message:
            job.error_message = error_message

        # Update completion time for final statuses
        if new_status in ["completed", "failed", "cancelled"]:
            job.completed_at = datetime.now(timezone.utc)

        # Update started time for processing status
        if new_status == "processing" and not job.started_at:
            job.started_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(job)
        return job

    def get_next_job(
        self,
        worker_id: str,
        supported_service_types: List[str]
    ) -> Optional[ProvisioningJob]:
        """Get the next job for a worker to process."""
        query = self.db.query(ProvisioningJob).filter(
            and_(
                ProvisioningJob.status == "queued",
                ProvisioningJob.service_type.in_(supported_service_types),
                or_(
                    ProvisioningJob.scheduled_for.is_(None),
                    ProvisioningJob.scheduled_for <= datetime.now(timezone.utc)
                )
            )
        ).order_by(
            # Priority order: urgent, high, normal, low
            func.case(
                (ProvisioningJob.priority == "urgent", 1),
                (ProvisioningJob.priority == "high", 2),
                (ProvisioningJob.priority == "normal", 3),
                (ProvisioningJob.priority == "low", 4),
                else_=5
            ),
            asc(ProvisioningJob.created_at)
        )

        job = query.first()
        if job:
            # Mark job as processing and assign to worker
            job.status = "processing"
            job.worker_id = worker_id
            job.started_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)

        return job

    def list_jobs(
        self,
        page: int = 1,
        per_page: int = 25,
        status: Optional[str] = None,
        service_type: Optional[str] = None,
        customer_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """List provisioning jobs with pagination and filtering."""
        query = self.db.query(ProvisioningJob)

        # Apply filters
        if status:
            query = query.filter(ProvisioningJob.status == status)
        if service_type:
            query = query.filter(ProvisioningJob.service_type == service_type)
        if customer_id:
            query = query.filter(ProvisioningJob.customer_id == customer_id)
        if priority:
            query = query.filter(ProvisioningJob.priority == priority)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        jobs = query.order_by(desc(ProvisioningJob.created_at)).offset(offset).limit(per_page).all()

        return {
            "jobs": jobs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    def cancel_job(self, job_id: str, reason: str) -> Optional[ProvisioningJob]:
        """Cancel a provisioning job."""
        job = self.get_by_job_id(job_id)
        if not job or job.status in ["completed", "failed", "cancelled"]:
            return None

        job.status = "cancelled"
        job.status_message = reason
        job.completed_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(job)
        return job

    def retry_job(self, job_id: str) -> Optional[ProvisioningJob]:
        """Retry a failed provisioning job."""
        job = self.get_by_job_id(job_id)
        if not job or job.status != "failed":
            return None

        job.status = "queued"
        job.retry_count = (job.retry_count or 0) + 1
        job.worker_id = None
        job.started_at = None
        job.completed_at = None
        job.error_message = None
        job.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(job)
        return job

    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get provisioning queue statistics."""
        stats = {}

        # Job counts by status
        status_counts = self.db.query(
            ProvisioningJob.status,
            func.count(ProvisioningJob.id)
        ).group_by(ProvisioningJob.status).all()

        stats["by_status"] = {status: count for status, count in status_counts}

        # Job counts by priority
        priority_counts = self.db.query(
            ProvisioningJob.priority,
            func.count(ProvisioningJob.id)
        ).group_by(ProvisioningJob.priority).all()

        stats["by_priority"] = {priority: count for priority, count in priority_counts}

        # Job counts by service type
        service_type_counts = self.db.query(
            ProvisioningJob.service_type,
            func.count(ProvisioningJob.id)
        ).group_by(ProvisioningJob.service_type).all()

        stats["by_service_type"] = {service_type: count for service_type, count in service_type_counts}

        # Average processing time for completed jobs
        avg_processing_time = self.db.query(
            func.avg(
                func.extract('epoch', ProvisioningJob.completed_at) -
                func.extract('epoch', ProvisioningJob.started_at)
            )
        ).filter(
            and_(
                ProvisioningJob.status == "completed",
                ProvisioningJob.started_at.isnot(None),
                ProvisioningJob.completed_at.isnot(None)
            )
        ).scalar()

        stats["avg_processing_time_seconds"] = float(avg_processing_time) if avg_processing_time else 0

        return stats

    def get_jobs_by_customer(self, customer_id: int) -> List[ProvisioningJob]:
        """Get all provisioning jobs for a specific customer."""
        return self.db.query(ProvisioningJob).filter(
            ProvisioningJob.customer_id == customer_id
        ).order_by(desc(ProvisioningJob.created_at)).all()

    def get_active_jobs(self) -> List[ProvisioningJob]:
        """Get all active (non-terminal) provisioning jobs."""
        return self.db.query(ProvisioningJob).filter(
            ProvisioningJob.status.in_(["queued", "processing"])
        ).order_by(asc(ProvisioningJob.created_at)).all()


class ProvisioningJobHistoryRepository(BaseRepository[ProvisioningJobHistory]):
    """Repository for provisioning job history management."""

    def __init__(self, db: Session):
        super().__init__(ProvisioningJobHistory, db)

    def create_history_entry(
        self,
        job_id: int,
        old_status: Optional[str],
        new_status: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None
    ) -> ProvisioningJobHistory:
        """Create a history entry for job status change."""
        history = ProvisioningJobHistory(
            job_id=job_id,
            old_status=old_status,
            new_status=new_status,
            message=message,
            details=details,
            created_by=created_by,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_job_history(self, job_id: int) -> List[ProvisioningJobHistory]:
        """Get history for a specific job."""
        return self.db.query(ProvisioningJobHistory).filter(
            ProvisioningJobHistory.job_id == job_id
        ).order_by(desc(ProvisioningJobHistory.created_at)).all()


class ProvisioningWorkerRepository(BaseRepository[ProvisioningWorkerStatus]):
    """Repository for provisioning worker management."""

    def __init__(self, db: Session):
        super().__init__(ProvisioningWorkerStatus, db)

    def register_worker(
        self,
        worker_id: str,
        worker_name: str,
        supported_service_types: List[str],
        max_concurrent_jobs: int = 1
    ) -> ProvisioningWorkerStatus:
        """Register or update a provisioning worker."""
        worker = self.db.query(ProvisioningWorkerStatus).filter(
            ProvisioningWorkerStatus.worker_id == worker_id
        ).first()

        if worker:
            # Update existing worker
            worker.worker_name = worker_name
            worker.supported_service_types = supported_service_types
            worker.max_concurrent_jobs = max_concurrent_jobs
            worker.last_heartbeat = datetime.now(timezone.utc)
            worker.updated_at = datetime.now(timezone.utc)
        else:
            # Create new worker
            worker = ProvisioningWorkerStatus(
                worker_id=worker_id,
                worker_name=worker_name,
                supported_service_types=supported_service_types,
                max_concurrent_jobs=max_concurrent_jobs,
                last_heartbeat=datetime.now(timezone.utc)
            )
            self.db.add(worker)

        self.db.commit()
        self.db.refresh(worker)
        return worker

    def update_worker_heartbeat(self, worker_id: str) -> Optional[ProvisioningWorkerStatus]:
        """Update worker heartbeat."""
        worker = self.db.query(ProvisioningWorkerStatus).filter(
            ProvisioningWorkerStatus.worker_id == worker_id
        ).first()

        if worker:
            worker.last_heartbeat = datetime.now(timezone.utc)
            worker.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(worker)

        return worker

    def get_active_workers(self) -> List[ProvisioningWorkerStatus]:
        """Get all active workers (heartbeat within last 5 minutes)."""
        cutoff_time = datetime.now(timezone.utc).replace(microsecond=0)
        cutoff_time = cutoff_time.replace(minute=cutoff_time.minute - 5)

        return self.db.query(ProvisioningWorkerStatus).filter(
            ProvisioningWorkerStatus.last_heartbeat >= cutoff_time
        ).all()
