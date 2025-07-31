"""
File Management API Endpoints

RESTful file management endpoints with proper resource-based routing.
Handles file uploads, downloads, metadata, and batch operations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.models.auth.base import Administrator
from app.models.file_storage import FileCategory, ImportStatus
from app.repositories.file_storage_repository import (
    ExportJobRepository,
    FileMetadataRepository,
    ImportJobRepository,
)
from app.schemas.file_storage import (
    CSVImportMapping,
    CSVImportPreview,
    ExportJobCreate,
    ExportJobListResponse,
    ExportJobResponse,
    FileListResponse,
    FileMetadataResponse,
    FileUploadResponse,
    ImportJobCreate,
    ImportJobListResponse,
    ImportJobResponse,
    PresignedUploadRequest,
)
from app.services.csv_import_service import CustomerCSVImporter
from app.services.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# File Management (RESTful Resource-Based)
# ============================================================================


@router.post("/", response_model=FileUploadResponse)
async def create_file_upload(
    request: PresignedUploadRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Create a presigned upload URL for file upload.

    Returns a presigned URL that clients can use to upload files directly to storage.
    """
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
        )

        return FileUploadResponse(
            file_id=result["file_id"],
            upload_url=result["upload_url"],
            expires_at=result["expires_at"],
        )
    except Exception as e:
        logger.error(f"Failed to create upload URL: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Upload URL creation failed: {str(e)}"
        )


@router.get("/", response_model=FileListResponse)
async def list_files(
    category: Optional[FileCategory] = Query(
        None, description="Filter by file category"
    ),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    ticket_id: Optional[int] = Query(None, description="Filter by ticket ID"),
    limit: int = Query(100, le=1000, description="Maximum number of files to return"),
    offset: int = Query(0, ge=0, description="Number of files to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """List files with optional filtering and pagination."""
    try:
        repo = FileMetadataRepository(db)

        files = repo.list_files(
            file_category=category,
            customer_id=customer_id,
            ticket_id=ticket_id,
            limit=limit,
            offset=offset,
        )

        total_count = repo.count_files(
            file_category=category, customer_id=customer_id, ticket_id=ticket_id
        )

        return FileListResponse(
            files=[FileMetadataResponse.from_orm(f) for f in files],
            total_count=total_count,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File listing failed: {str(e)}")


@router.get("/{file_id}", response_model=FileMetadataResponse)
async def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get file metadata by ID."""
    try:
        repo = FileMetadataRepository(db)
        file_metadata = repo.get_file(file_id)

        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")

        return FileMetadataResponse.from_orm(file_metadata)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File retrieval failed: {str(e)}")


@router.get("/{file_id}/download")
async def get_file_download_url(
    file_id: int,
    expires_in: int = Query(
        3600, le=86400, description="URL expiration time in seconds"
    ),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get presigned download URL for a file."""
    try:
        service = FileStorageService(db)
        download_url = await service.get_download_url(file_id, expires_in)

        return {
            "download_url": download_url,
            "expires_in": expires_in,
            "file_id": file_id,
        }
    except Exception as e:
        logger.error(f"Failed to get download URL for file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Download URL generation failed: {str(e)}"
        )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Delete a file and its metadata."""
    try:
        service = FileStorageService(db)
        await service.delete_file(file_id)

        return {"message": "File deleted successfully", "file_id": file_id}
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")


# ============================================================================
# Import Operations (Sub-resource of Files)
# ============================================================================


@router.post("/imports", response_model=ImportJobResponse)
async def create_import_job(
    request: ImportJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create a new CSV import job."""
    try:
        repo = ImportJobRepository(db)

        # Create import job record
        import_job = repo.create_import_job(
            file_id=request.file_id,
            import_type=request.import_type,
            created_by=current_admin.id,
            options=request.options,
        )

        # Add background task for processing
        if request.import_type == "customers":
            background_tasks.add_task(
                _process_customer_import, db, import_job.id, current_admin.id
            )

        return ImportJobResponse.from_orm(import_job)
    except Exception as e:
        logger.error(f"Failed to create import job: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Import job creation failed: {str(e)}"
        )


@router.get("/imports", response_model=ImportJobListResponse)
async def list_import_jobs(
    status: Optional[ImportStatus] = Query(None, description="Filter by import status"),
    import_type: Optional[str] = Query(None, description="Filter by import type"),
    limit: int = Query(50, le=500, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """List import jobs with optional filtering."""
    try:
        repo = ImportJobRepository(db)

        jobs = repo.list_import_jobs(
            status=status, import_type=import_type, limit=limit, offset=offset
        )

        total_count = repo.count_import_jobs(status=status, import_type=import_type)

        return ImportJobListResponse(
            jobs=[ImportJobResponse.from_orm(job) for job in jobs],
            total_count=total_count,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Failed to list import jobs: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Import job listing failed: {str(e)}"
        )


@router.get("/imports/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get import job details by ID."""
    try:
        repo = ImportJobRepository(db)
        job = repo.get_import_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Import job not found")

        return ImportJobResponse.from_orm(job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get import job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Import job retrieval failed: {str(e)}"
        )


@router.get("/imports/{job_id}/preview", response_model=CSVImportPreview)
async def get_import_preview(
    job_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get CSV preview for import job."""
    try:
        importer = CustomerCSVImporter(db)
        preview = await importer.preview_import(job_id)

        return CSVImportPreview(
            headers=preview["headers"],
            sample_rows=preview["sample_rows"],
            total_rows=preview["total_rows"],
            suggested_mapping=preview.get("suggested_mapping", {}),
        )
    except Exception as e:
        logger.error(f"Failed to get import preview for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import preview failed: {str(e)}")


@router.post("/imports/{job_id}/process")
async def process_import_job(
    job_id: int,
    mapping: CSVImportMapping,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Process import job with column mapping."""
    try:
        repo = ImportJobRepository(db)
        job = repo.get_import_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Import job not found")

        if job.status != ImportStatus.PENDING:
            raise HTTPException(
                status_code=400, detail="Import job is not in pending status"
            )

        # Update job with mapping and start processing
        repo.update_import_job(
            job_id,
            {
                "column_mapping": mapping.column_mapping,
                "status": ImportStatus.PROCESSING,
            },
        )

        # Add background task for processing
        background_tasks.add_task(
            _process_customer_import_with_mapping,
            db,
            job_id,
            mapping.column_mapping,
            current_admin.id,
        )

        return {"message": "Import job processing started", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process import job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Import processing failed: {str(e)}"
        )


# ============================================================================
# Export Operations (Sub-resource of Files)
# ============================================================================


@router.post("/exports", response_model=ExportJobResponse)
async def create_export_job(
    request: ExportJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create a new export job."""
    try:
        repo = ExportJobRepository(db)

        export_job = repo.create_export_job(
            export_type=request.export_type,
            file_format=request.file_format,
            created_by=current_admin.id,
            filters=request.filters,
            options=request.options,
        )

        # Add background task for processing
        background_tasks.add_task(
            _process_export_job, db, export_job.id, current_admin.id
        )

        return ExportJobResponse.from_orm(export_job)
    except Exception as e:
        logger.error(f"Failed to create export job: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Export job creation failed: {str(e)}"
        )


@router.get("/exports", response_model=ExportJobListResponse)
async def list_export_jobs(
    status: Optional[ImportStatus] = Query(None, description="Filter by export status"),
    export_type: Optional[str] = Query(None, description="Filter by export type"),
    limit: int = Query(50, le=500, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """List export jobs with optional filtering."""
    try:
        repo = ExportJobRepository(db)

        jobs = repo.list_export_jobs(
            status=status, export_type=export_type, limit=limit, offset=offset
        )

        total_count = repo.count_export_jobs(status=status, export_type=export_type)

        return ExportJobListResponse(
            jobs=[ExportJobResponse.from_orm(job) for job in jobs],
            total_count=total_count,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Failed to list export jobs: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Export job listing failed: {str(e)}"
        )


@router.get("/exports/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get export job details by ID."""
    try:
        repo = ExportJobRepository(db)
        job = repo.get_export_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        return ExportJobResponse.from_orm(job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get export job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Export job retrieval failed: {str(e)}"
        )


# ============================================================================
# Background Task Functions
# ============================================================================


async def _process_customer_import(db: Session, job_id: int, admin_id: int):
    """Background task to process customer CSV import."""
    try:
        importer = CustomerCSVImporter(db)
        await importer.process_import(job_id, admin_id)
    except Exception as e:
        logger.error(f"Failed to process customer import job {job_id}: {str(e)}")


async def _process_customer_import_with_mapping(
    db: Session, job_id: int, column_mapping: dict, admin_id: int
):
    """Background task to process customer CSV import with column mapping."""
    try:
        importer = CustomerCSVImporter(db)
        await importer.process_import_with_mapping(job_id, column_mapping, admin_id)
    except Exception as e:
        logger.error(
            f"Failed to process customer import job {job_id} with mapping: {str(e)}"
        )


async def _process_export_job(db: Session, job_id: int, admin_id: int):
    """Background task to process export job."""
    try:
        # Implementation depends on export type
        logger.info(f"Processing export job {job_id} for admin {admin_id}")
        # TODO: Implement export processing logic
    except Exception as e:
        logger.error(f"Failed to process export job {job_id}: {str(e)}")
