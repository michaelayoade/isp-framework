"""
File Storage API Endpoints

REST API endpoints for file uploads/downloads, CSV imports, ticket attachments,
and MinIO S3 integration.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db, SessionLocal
from app.api.dependencies import get_current_admin
from app.models.auth.base import Administrator
from app.models.file_storage import FileCategory, FileStatus, ImportStatus
from app.schemas.file_storage import (
    FileUploadResponse, FileMetadataResponse, FileListResponse,
    PresignedUploadRequest, ImportJobCreate, ImportJobResponse,
    ImportJobListResponse, CSVImportPreview, CSVImportMapping,
    ExportJobCreate, ExportJobResponse, ExportJobListResponse
)
from app.services.file_storage_service import FileStorageService
from app.services.csv_import_service import CustomerCSVImporter
from app.repositories.file_storage_repository import (
    FileMetadataRepository, ImportJobRepository, ExportJobRepository
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["file-storage"])


@router.post("/upload-url", response_model=FileUploadResponse)
async def get_upload_url(
    request: PresignedUploadRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get presigned upload URL for file"""
    
    service = FileStorageService(db)
    
    try:
        result = await service.upload_file(
            filename=request.filename,
            file_size=request.file_size,
            mime_type=request.mime_type,
            category=request.file_category,
            uploaded_by=current_admin.id,
            customer_id=request.customer_id,
            ticket_id=request.ticket_id,
            metadata=request.metadata
        )
        
        return FileUploadResponse(
            file_id=result["file_id"],
            filename=request.filename,
            file_size=request.file_size,
            mime_type=request.mime_type,
            upload_url=result["upload_url"],
            expires_at=result["expires_at"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating upload URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/files", response_model=FileListResponse)
async def list_files(
    file_category: Optional[FileCategory] = None,
    customer_id: Optional[int] = None,
    ticket_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List files with optional filtering"""
    
    repo = FileMetadataRepository(db)
    
    query = db.query(repo.model)
    
    if file_category:
        query = query.filter(repo.model.file_category == file_category)
    
    if customer_id:
        query = query.filter(repo.model.customer_id == customer_id)
    
    if ticket_id:
        query = query.filter(repo.model.ticket_id == ticket_id)
    
    total = query.count()
    files = query.order_by(repo.model.created_at.desc()).limit(limit).offset(offset).all()
    
    return FileListResponse(
        items=[FileMetadataResponse.from_orm(file) for file in files],
        total=total,
        page=offset // limit + 1,
        pages=(total + limit - 1) // limit,
        limit=limit
    )


@router.get("/files/{file_id}", response_model=FileMetadataResponse)
async def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get file metadata"""
    
    repo = FileMetadataRepository(db)
    file_record = repo.get_by_id(file_id)
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileMetadataResponse.from_orm(file_record)


@router.get("/files/{file_id}/download")
async def get_download_url(
    file_id: int,
    expires_in: int = 3600,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get presigned download URL"""
    
    service = FileStorageService(db)
    
    try:
        download_url = await service.get_download_url(file_id, expires_in)
        return {"download_url": download_url, "expires_in": expires_in}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating download URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Delete file"""
    
    service = FileStorageService(db)
    
    try:
        success = await service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/imports", response_model=ImportJobResponse)
async def create_import_job(
    request: ImportJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create customer CSV import job"""
    
    file_repo = FileMetadataRepository(db)
    import_repo = ImportJobRepository(db)
    
    # Verify file exists and is CSV
    file_record = file_repo.get_by_id(request.file_metadata_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_record.mime_type not in ['text/csv', 'application/vnd.ms-excel']:
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    # Create import job
    job_name = f"Customer Import - {file_record.filename}"
    import_job = import_repo.create_import_job(
        job_name=job_name,
        file_metadata_id=request.file_metadata_id,
        import_type=request.import_type,
        import_config=request.import_config,
        created_by=current_admin.id
    )
    
    # Update file status
    file_repo.update_file_status(file_record.id, FileStatus.PROCESSING)
    
    # Queue background task (using threading for now, Celery in production)
    from threading import Thread
    def run_import():
        db_session = SessionLocal()
        try:
            importer = CustomerCSVImporter(db_session)
            importer.process_customer_csv_import(import_job.id)
        finally:
            db_session.close()
    
    Thread(target=run_import).start()
    
    return ImportJobResponse.from_orm(import_job)


@router.get("/imports", response_model=ImportJobListResponse)
async def list_import_jobs(
    status: Optional[ImportStatus] = None,
    import_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List import jobs"""
    
    repo = ImportJobRepository(db)
    
    query = db.query(repo.model)
    
    if status:
        query = query.filter(repo.model.status == status)
    
    if import_type:
        query = query.filter(repo.model.import_type == import_type)
    
    total = query.count()
    jobs = query.order_by(repo.model.created_at.desc()).limit(limit).offset(offset).all()
    
    return ImportJobListResponse(
        items=[ImportJobResponse.from_orm(job) for job in jobs],
        total=total,
        page=offset // limit + 1,
        pages=(total + limit - 1) // limit,
        limit=limit
    )


@router.get("/imports/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get import job details"""
    
    repo = ImportJobRepository(db)
    job = repo.get_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    return ImportJobResponse.from_orm(job)


@router.get("/imports/{job_id}/preview", response_model=CSVImportPreview)
async def get_import_preview(
    job_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get CSV preview for import job"""
    
    import_repo = ImportJobRepository(db)
    job = import_repo.get_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    importer = CustomerCSVImporter(db)
    
    try:
        preview = importer.get_csv_preview(job.file_metadata_id)
        return preview
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting CSV preview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/imports/{job_id}/process")
async def process_import_job(
    job_id: int,
    mapping: CSVImportMapping,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Process import job with column mapping"""
    
    import_repo = ImportJobRepository(db)
    job = import_repo.get_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    if job.status != ImportStatus.PENDING:
        raise HTTPException(status_code=400, detail="Job is not in pending state")
    
    # Update import config with mapping
    job.import_config.update({
        'column_mapping': mapping.column_mapping,
        'skip_errors': mapping.skip_errors,
        'update_existing': mapping.update_existing
    })
    db.commit()
    
    # Start processing
    from threading import Thread
    def run_import():
        db_session = SessionLocal()
        try:
            importer = CustomerCSVImporter(db_session)
            importer.process_customer_csv_import(job_id)
        finally:
            db_session.close()
    
    Thread(target=run_import).start()
    
    return {"message": "Import job started processing"}


@router.post("/exports", response_model=ExportJobResponse)
async def create_export_job(
    request: ExportJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create export job"""
    
    repo = ExportJobRepository(db)
    
    job = repo.create_export_job(
        job_name=request.job_name,
        export_type=request.export_type,
        export_config=request.export_config,
        file_format=request.file_format,
        created_by=current_admin.id
    )
    
    # TODO: Implement background export processing
    
    return ExportJobResponse.from_orm(job)


@router.get("/exports", response_model=ExportJobListResponse)
async def list_export_jobs(
    status: Optional[ImportStatus] = None,
    export_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List export jobs"""
    
    repo = ExportJobRepository(db)
    
    query = db.query(repo.model)
    
    if status:
        query = query.filter(repo.model.status == status)
    
    if export_type:
        query = query.filter(repo.model.export_type == export_type)
    
    total = query.count()
    jobs = query.order_by(repo.model.created_at.desc()).limit(limit).offset(offset).all()
    
    return ExportJobListResponse(
        items=[ExportJobResponse.from_orm(job) for job in jobs],
        total=total,
        page=offset // limit + 1,
        pages=(total + limit - 1) // limit,
        limit=limit
    )


@router.get("/exports/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get export job details"""
    
    repo = ExportJobRepository(db)
    job = repo.get_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    return ExportJobResponse.from_orm(job)
