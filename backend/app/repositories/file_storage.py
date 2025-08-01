"""
File Storage Repository

Repository layer for file storage management including:
- File metadata CRUD operations
- Import/Export job management
- File permissions and access control
- MinIO S3 integration support
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import Session, joinedload

from app.models.file_storage import (
    FileMetadata,
    ImportJob,
    ExportJob,
    FilePermission,
    FileCategory,
    FileStatus,
    ImportStatus
)
from app.repositories.base import BaseRepository


class FileRepository(BaseRepository[FileMetadata]):
    """Repository for file metadata management."""

    def __init__(self, db: Session):
        super().__init__(FileMetadata, db)

    def create_file_metadata(
        self,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        file_category: FileCategory,
        bucket_name: str,
        object_key: str,
        uploaded_by: int,
        customer_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        checksum: Optional[str] = None,
        file_metadata: Optional[Dict[str, Any]] = None
    ) -> FileMetadata:
        """Create file metadata record."""
        file_record = FileMetadata(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            file_category=file_category,
            bucket_name=bucket_name,
            object_key=object_key,
            uploaded_by=uploaded_by,
            customer_id=customer_id,
            ticket_id=ticket_id,
            checksum=checksum,
            file_metadata=file_metadata or {},
            file_status=FileStatus.UPLOADED
        )
        self.db.add(file_record)
        self.db.commit()
        self.db.refresh(file_record)
        return file_record

    def get_by_path(self, file_path: str) -> Optional[FileMetadata]:
        """Get file metadata by file path."""
        return self.db.query(FileMetadata).filter(
            FileMetadata.file_path == file_path
        ).first()

    def get_by_object_key(self, bucket_name: str, object_key: str) -> Optional[FileMetadata]:
        """Get file metadata by bucket and object key."""
        return self.db.query(FileMetadata).filter(
            and_(
                FileMetadata.bucket_name == bucket_name,
                FileMetadata.object_key == object_key
            )
        ).first()

    def list_files(
        self,
        page: int = 1,
        per_page: int = 25,
        file_category: Optional[FileCategory] = None,
        file_status: Optional[FileStatus] = None,
        customer_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        uploaded_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """List files with pagination and filtering."""
        query = self.db.query(FileMetadata)

        # Apply filters
        if file_category:
            query = query.filter(FileMetadata.file_category == file_category)
        if file_status:
            query = query.filter(FileMetadata.file_status == file_status)
        if customer_id:
            query = query.filter(FileMetadata.customer_id == customer_id)
        if ticket_id:
            query = query.filter(FileMetadata.ticket_id == ticket_id)
        if uploaded_by:
            query = query.filter(FileMetadata.uploaded_by == uploaded_by)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        files = query.order_by(desc(FileMetadata.created_at)).offset(offset).limit(per_page).all()

        return {
            "files": files,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    def update_file_status(
        self,
        file_id: int,
        new_status: FileStatus,
        processed_at: Optional[datetime] = None
    ) -> Optional[FileMetadata]:
        """Update file status."""
        file_record = self.get(file_id)
        if not file_record:
            return None

        file_record.file_status = new_status
        file_record.updated_at = datetime.now(timezone.utc)
        
        if processed_at:
            file_record.processed_at = processed_at
        elif new_status == FileStatus.PROCESSED:
            file_record.processed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(file_record)
        return file_record

    def update_presigned_url(
        self,
        file_id: int,
        presigned_url: str,
        expires_at: datetime
    ) -> Optional[FileMetadata]:
        """Update presigned URL and expiration."""
        file_record = self.get(file_id)
        if not file_record:
            return None

        file_record.presigned_url = presigned_url
        file_record.url_expires_at = expires_at
        file_record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(file_record)
        return file_record

    def get_files_by_customer(self, customer_id: int) -> List[FileMetadata]:
        """Get all files for a specific customer."""
        return self.db.query(FileMetadata).filter(
            FileMetadata.customer_id == customer_id
        ).order_by(desc(FileMetadata.created_at)).all()

    def get_files_by_ticket(self, ticket_id: int) -> List[FileMetadata]:
        """Get all files for a specific ticket."""
        return self.db.query(FileMetadata).filter(
            FileMetadata.ticket_id == ticket_id
        ).order_by(desc(FileMetadata.created_at)).all()

    def get_expired_presigned_urls(self) -> List[FileMetadata]:
        """Get files with expired presigned URLs."""
        return self.db.query(FileMetadata).filter(
            and_(
                FileMetadata.presigned_url.isnot(None),
                FileMetadata.url_expires_at < datetime.now(timezone.utc)
            )
        ).all()

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get file storage statistics."""
        stats = {}

        # File counts by category
        category_counts = self.db.query(
            FileMetadata.file_category,
            func.count(FileMetadata.id)
        ).group_by(FileMetadata.file_category).all()

        stats["by_category"] = {category.value: count for category, count in category_counts}

        # File counts by status
        status_counts = self.db.query(
            FileMetadata.file_status,
            func.count(FileMetadata.id)
        ).group_by(FileMetadata.file_status).all()

        stats["by_status"] = {status.value: count for status, count in status_counts}

        # Total storage size
        total_size = self.db.query(func.sum(FileMetadata.file_size)).scalar() or 0
        stats["total_size_bytes"] = total_size

        # Storage size by category
        size_by_category = self.db.query(
            FileMetadata.file_category,
            func.sum(FileMetadata.file_size)
        ).group_by(FileMetadata.file_category).all()

        stats["size_by_category"] = {
            category.value: size or 0 for category, size in size_by_category
        }

        return stats


class ImportJobRepository(BaseRepository[ImportJob]):
    """Repository for import job management."""

    def __init__(self, db: Session):
        super().__init__(ImportJob, db)

    def create_import_job(
        self,
        job_name: str,
        file_metadata_id: int,
        import_type: str,
        created_by: int,
        import_config: Optional[Dict[str, Any]] = None
    ) -> ImportJob:
        """Create a new import job."""
        job = ImportJob(
            job_name=job_name,
            file_metadata_id=file_metadata_id,
            import_type=import_type,
            created_by=created_by,
            import_config=import_config or {},
            status=ImportStatus.PENDING
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job_progress(
        self,
        job_id: int,
        status: ImportStatus,
        progress_percent: int,
        processed_records: int,
        failed_records: int = 0,
        error_message: Optional[str] = None,
        validation_errors: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[ImportJob]:
        """Update import job progress."""
        job = self.get(job_id)
        if not job:
            return None

        job.status = status
        job.progress_percent = progress_percent
        job.processed_records = processed_records
        job.failed_records = failed_records
        job.updated_at = datetime.now(timezone.utc)

        if error_message:
            job.error_message = error_message
        if validation_errors:
            job.validation_errors = validation_errors

        # Update timing fields
        if status == ImportStatus.PROCESSING and not job.processing_started_at:
            job.processing_started_at = datetime.now(timezone.utc)
        elif status in [ImportStatus.COMPLETED, ImportStatus.FAILED, ImportStatus.CANCELLED]:
            job.processing_completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(job)
        return job

    def get_active_jobs(self) -> List[ImportJob]:
        """Get all active import jobs."""
        return self.db.query(ImportJob).filter(
            ImportJob.status.in_([ImportStatus.PENDING, ImportStatus.PROCESSING])
        ).order_by(asc(ImportJob.created_at)).all()

    def get_jobs_by_type(self, import_type: str) -> List[ImportJob]:
        """Get import jobs by type."""
        return self.db.query(ImportJob).filter(
            ImportJob.import_type == import_type
        ).order_by(desc(ImportJob.created_at)).all()


class ExportJobRepository(BaseRepository[ExportJob]):
    """Repository for export job management."""

    def __init__(self, db: Session):
        super().__init__(ExportJob, db)

    def create_export_job(
        self,
        job_name: str,
        export_type: str,
        created_by: int,
        export_config: Optional[Dict[str, Any]] = None,
        file_format: str = "csv"
    ) -> ExportJob:
        """Create a new export job."""
        job = ExportJob(
            job_name=job_name,
            export_type=export_type,
            created_by=created_by,
            export_config=export_config or {},
            file_format=file_format,
            status=ImportStatus.PENDING
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job_progress(
        self,
        job_id: int,
        status: ImportStatus,
        progress_percent: int,
        processed_records: int,
        output_file_metadata_id: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[ExportJob]:
        """Update export job progress."""
        job = self.get(job_id)
        if not job:
            return None

        job.status = status
        job.progress_percent = progress_percent
        job.processed_records = processed_records
        job.updated_at = datetime.now(timezone.utc)

        if output_file_metadata_id:
            job.output_file_metadata_id = output_file_metadata_id
        if error_message:
            job.error_message = error_message

        # Update timing fields
        if status == ImportStatus.PROCESSING and not job.processing_started_at:
            job.processing_started_at = datetime.now(timezone.utc)
        elif status in [ImportStatus.COMPLETED, ImportStatus.FAILED, ImportStatus.CANCELLED]:
            job.processing_completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(job)
        return job

    def get_active_jobs(self) -> List[ExportJob]:
        """Get all active export jobs."""
        return self.db.query(ExportJob).filter(
            ExportJob.status.in_([ImportStatus.PENDING, ImportStatus.PROCESSING])
        ).order_by(asc(ExportJob.created_at)).all()


class FilePermissionRepository(BaseRepository[FilePermission]):
    """Repository for file permission management."""

    def __init__(self, db: Session):
        super().__init__(FilePermission, db)

    def create_permission(
        self,
        file_metadata_id: int,
        is_public: bool = False,
        allowed_customers: Optional[List[int]] = None,
        allowed_roles: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> FilePermission:
        """Create file permission."""
        permission = FilePermission(
            file_metadata_id=file_metadata_id,
            is_public=is_public,
            allowed_customers=allowed_customers or [],
            allowed_roles=allowed_roles or [],
            expires_at=expires_at
        )
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def check_access(
        self,
        file_metadata_id: int,
        customer_id: Optional[int] = None,
        user_roles: Optional[List[str]] = None
    ) -> bool:
        """Check if user has access to file."""
        permission = self.db.query(FilePermission).filter(
            FilePermission.file_metadata_id == file_metadata_id
        ).first()

        if not permission:
            return False

        # Check if permission is expired
        if permission.expires_at and permission.expires_at < datetime.now(timezone.utc):
            return False

        # Check public access
        if permission.is_public:
            return True

        # Check customer access
        if customer_id and customer_id in permission.allowed_customers:
            return True

        # Check role access
        if user_roles:
            for role in user_roles:
                if role in permission.allowed_roles:
                    return True

        return False

    def get_expired_permissions(self) -> List[FilePermission]:
        """Get expired file permissions."""
        return self.db.query(FilePermission).filter(
            and_(
                FilePermission.expires_at.isnot(None),
                FilePermission.expires_at < datetime.now(timezone.utc)
            )
        ).all()
