"""
File Storage Repository for MinIO S3 Integration

Repository pattern implementation for file metadata, import/export jobs,
and file permission management.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.file_storage import (
    FileMetadata, FileCategory, FileStatus, 
    ImportJob, ExportJob, ImportStatus
)
from app.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)


class FileMetadataRepository(BaseRepository[FileMetadata]):
    """Repository for file metadata operations"""
    
    def __init__(self, db: Session):
        super().__init__(FileMetadata, db)
    
    def create_file_metadata(
        self,
        filename: str,
        file_size: int,
        mime_type: str,
        category: FileCategory,
        uploaded_by: int,
        bucket_name: str,
        object_key: str,
        customer_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        checksum: Optional[str] = None
    ) -> FileMetadata:
        """Create new file metadata record"""
        
        file_record = FileMetadata(
            filename=filename,
            original_filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            file_category=category,
            uploaded_by=uploaded_by,
            customer_id=customer_id,
            ticket_id=ticket_id,
            bucket_name=bucket_name,
            object_key=object_key,
            metadata=metadata or {},
            checksum=checksum
        )
        
        self.db.add(file_record)
        self.db.commit()
        self.db.refresh(file_record)
        
        return file_record
    
    def get_by_id(self, file_id: int) -> Optional[FileMetadata]:
        """Get file metadata by ID"""
        return self.db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
    
    def get_by_object_key(self, bucket_name: str, object_key: str) -> Optional[FileMetadata]:
        """Get file metadata by bucket and object key"""
        return self.db.query(FileMetadata).filter(
            and_(
                FileMetadata.bucket_name == bucket_name,
                FileMetadata.object_key == object_key
            )
        ).first()
    
    def update_file_status(
        self,
        file_id: int,
        status: FileStatus,
        processed_at: Optional[datetime] = None
    ) -> Optional[FileMetadata]:
        """Update file processing status"""
        
        file_record = self.get_by_id(file_id)
        if file_record:
            file_record.file_status = status
            if processed_at:
                file_record.processed_at = processed_at
            elif status == FileStatus.PROCESSED:
                file_record.processed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(file_record)
        
        return file_record
    
    def get_files_by_category(
        self,
        category: FileCategory,
        customer_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FileMetadata]:
        """Get files by category with optional filters"""
        
        query = self.db.query(FileMetadata).filter(
            FileMetadata.file_category == category
        )
        
        if customer_id:
            query = query.filter(FileMetadata.customer_id == customer_id)
        
        if ticket_id:
            query = query.filter(FileMetadata.ticket_id == ticket_id)
        
        return query.order_by(desc(FileMetadata.created_at)).limit(limit).offset(offset).all()
    
    def search_files(
        self,
        search_term: str,
        category: Optional[FileCategory] = None,
        customer_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FileMetadata]:
        """Search files by filename or metadata"""
        
        query = self.db.query(FileMetadata)
        
        if search_term:
            query = query.filter(
                or_(
                    FileMetadata.filename.ilike(f"%{search_term}%"),
                    FileMetadata.original_filename.ilike(f"%{search_term}%"),
                    FileMetadata.metadata.cast(str).ilike(f"%{search_term}%")
                )
            )
        
        if category:
            query = query.filter(FileMetadata.file_category == category)
        
        if customer_id:
            query = query.filter(FileMetadata.customer_id == customer_id)
        
        return query.order_by(desc(FileMetadata.created_at)).limit(limit).offset(offset).all()
    
    def get_file_count(
        self,
        category: Optional[FileCategory] = None,
        customer_id: Optional[int] = None
    ) -> int:
        """Get count of files with optional filters"""
        
        query = self.db.query(FileMetadata)
        
        if category:
            query = query.filter(FileMetadata.file_category == category)
        
        if customer_id:
            query = query.filter(FileMetadata.customer_id == customer_id)
        
        return query.count()
    
    def delete_file_metadata(self, file_id: int) -> bool:
        """Delete file metadata record"""
        
        file_record = self.get_by_id(file_id)
        if file_record:
            self.db.delete(file_record)
            self.db.commit()
            return True
        
        return False


class ImportJobRepository(BaseRepository[ImportJob]):
    """Repository for import job operations"""
    
    def __init__(self, db: Session):
        super().__init__(ImportJob, db)
    
    def create_import_job(
        self,
        job_name: str,
        file_metadata_id: int,
        import_type: str,
        import_config: Optional[Dict[str, Any]] = None,
        created_by: int = None
    ) -> ImportJob:
        """Create new import job"""
        
        import_job = ImportJob(
            job_name=job_name,
            file_metadata_id=file_metadata_id,
            import_type=import_type,
            import_config=import_config or {},
            created_by=created_by
        )
        
        self.db.add(import_job)
        self.db.commit()
        self.db.refresh(import_job)
        
        return import_job
    
    def get_by_id(self, job_id: int) -> Optional[ImportJob]:
        """Get import job by ID"""
        return self.db.query(ImportJob).filter(ImportJob.id == job_id).first()
    
    def update_job_status(
        self,
        job_id: int,
        status: ImportStatus,
        progress_percent: Optional[int] = None,
        total_records: Optional[int] = None,
        processed_records: Optional[int] = None,
        failed_records: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[ImportJob]:
        """Update import job status and progress"""
        
        job = self.get_by_id(job_id)
        if job:
            job.status = status
            
            if progress_percent is not None:
                job.progress_percent = progress_percent
            
            if total_records is not None:
                job.total_records = total_records
            
            if processed_records is not None:
                job.processed_records = processed_records
            
            if failed_records is not None:
                job.failed_records = failed_records
            
            if error_message is not None:
                job.error_message = error_message
            
            if status == ImportStatus.PROCESSING and not job.processing_started_at:
                job.processing_started_at = datetime.utcnow()
            
            if status in [ImportStatus.COMPLETED, ImportStatus.FAILED] and not job.processing_completed_at:
                job.processing_completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(job)
        
        return job
    
    def get_jobs_by_status(
        self,
        status: ImportStatus,
        import_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImportJob]:
        """Get import jobs by status"""
        
        query = self.db.query(ImportJob).filter(ImportJob.status == status)
        
        if import_type:
            query = query.filter(ImportJob.import_type == import_type)
        
        return query.order_by(desc(ImportJob.created_at)).limit(limit).offset(offset).all()
    
    def get_pending_jobs(self, import_type: Optional[str] = None) -> List[ImportJob]:
        """Get pending import jobs"""
        return self.get_jobs_by_status(ImportStatus.PENDING, import_type)
    
    def get_jobs_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImportJob]:
        """Get import jobs created by specific user"""
        
        return self.db.query(ImportJob).filter(
            ImportJob.created_by == user_id
        ).order_by(desc(ImportJob.created_at)).limit(limit).offset(offset).all()


class ExportJobRepository(BaseRepository[ExportJob]):
    """Repository for export job operations"""
    
    def __init__(self, db: Session):
        super().__init__(ExportJob, db)
    
    def create_export_job(
        self,
        job_name: str,
        export_type: str,
        export_config: Optional[Dict[str, Any]] = None,
        file_format: str = "csv",
        created_by: int = None
    ) -> ExportJob:
        """Create new export job"""
        
        export_job = ExportJob(
            job_name=job_name,
            export_type=export_type,
            export_config=export_config or {},
            file_format=file_format,
            created_by=created_by
        )
        
        self.db.add(export_job)
        self.db.commit()
        self.db.refresh(export_job)
        
        return export_job
    
    def get_by_id(self, job_id: int) -> Optional[ExportJob]:
        """Get export job by ID"""
        return self.db.query(ExportJob).filter(ExportJob.id == job_id).first()
    
    def update_job_status(
        self,
        job_id: int,
        status: ImportStatus,
        progress_percent: Optional[int] = None,
        total_records: Optional[int] = None,
        processed_records: Optional[int] = None,
        output_file_id: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[ExportJob]:
        """Update export job status and progress"""
        
        job = self.get_by_id(job_id)
        if job:
            job.status = status
            
            if progress_percent is not None:
                job.progress_percent = progress_percent
            
            if total_records is not None:
                job.total_records = total_records
            
            if processed_records is not None:
                job.processed_records = processed_records
            
            if output_file_id is not None:
                job.output_file_metadata_id = output_file_id
            
            if error_message is not None:
                job.error_message = error_message
            
            if status == ImportStatus.PROCESSING and not job.processing_started_at:
                job.processing_started_at = datetime.utcnow()
            
            if status in [ImportStatus.COMPLETED, ImportStatus.FAILED] and not job.processing_completed_at:
                job.processing_completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(job)
        
        return job
