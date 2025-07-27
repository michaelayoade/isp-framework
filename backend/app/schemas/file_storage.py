"""
File Storage Schemas for MinIO S3 Integration

Pydantic schemas for file management, CSV imports, ticket attachments,
and MinIO S3 operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.file_storage import FileCategory, FileStatus, ImportStatus


class FileUploadResponse(BaseModel):
    """Response for file upload operations"""
    file_id: int
    filename: str
    file_size: int
    mime_type: str
    upload_url: str
    expires_at: datetime


class FileMetadataResponse(BaseModel):
    """Response for file metadata"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    file_category: FileCategory
    file_status: FileStatus
    customer_id: Optional[int] = None
    ticket_id: Optional[int] = None
    uploaded_by: int
    bucket_name: str
    object_key: str
    metadata: Dict[str, Any] = {}
    checksum: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """Paginated file list response"""
    items: List[FileMetadataResponse]
    total: int
    page: int
    pages: int
    limit: int


class FileFilter(BaseModel):
    """Filter parameters for file listing"""
    file_category: Optional[FileCategory] = None
    customer_id: Optional[int] = None
    ticket_id: Optional[int] = None
    uploaded_by: Optional[int] = None
    file_status: Optional[FileStatus] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class PresignedUploadRequest(BaseModel):
    """Request for presigned upload URL"""
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, le=104857600)  # 100MB max
    mime_type: str = Field(..., max_length=100)
    file_category: FileCategory
    customer_id: Optional[int] = None
    ticket_id: Optional[int] = None
    metadata: Dict[str, Any] = {}

    @validator('filename')
    def validate_filename(cls, v):
        if not v.strip():
            raise ValueError('Filename cannot be empty')
        return v.strip()

    @validator('mime_type')
    def validate_mime_type(cls, v):
        allowed_types = [
            'text/csv', 'application/vnd.ms-excel',
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain',
            'application/json', 'application/xml'
        ]
        if v not in allowed_types:
            raise ValueError(f'Unsupported file type: {v}')
        return v


class ImportJobCreate(BaseModel):
    """Request to create an import job"""
    file_metadata_id: int
    import_type: str = Field(..., pattern="^(customer_csv|service_csv|billing_csv)$")
    import_config: Dict[str, Any] = Field(default_factory=dict)


class ImportJobResponse(BaseModel):
    """Response for import job"""
    id: int
    job_name: str
    file_metadata_id: int
    import_type: str
    status: ImportStatus
    progress_percent: int
    total_records: int
    processed_records: int
    failed_records: int
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    validation_errors: List[Dict[str, Any]] = []
    import_config: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ImportJobListResponse(BaseModel):
    """Paginated import job list"""
    items: List[ImportJobResponse]
    total: int
    page: int
    pages: int
    limit: int


class ExportJobCreate(BaseModel):
    """Request to create an export job"""
    job_name: str = Field(..., min_length=1, max_length=255)
    export_type: str = Field(..., pattern="^(customer_export|billing_export|service_export)$")
    export_config: Dict[str, Any] = Field(default_factory=dict)
    file_format: str = Field(default="csv", pattern="^(csv|xlsx|json)$")


class ExportJobResponse(BaseModel):
    """Response for export job"""
    id: int
    job_name: str
    export_type: str
    file_format: str
    status: ImportStatus
    progress_percent: int
    total_records: int
    processed_records: int
    export_config: Dict[str, Any] = {}
    output_file_metadata_id: Optional[int] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExportJobListResponse(BaseModel):
    """Paginated export job list"""
    items: List[ExportJobResponse]
    total: int
    page: int
    pages: int
    limit: int


class FilePermissionUpdate(BaseModel):
    """Update file permissions"""
    is_public: Optional[bool] = None
    allowed_customers: Optional[List[int]] = None
    allowed_roles: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class CSVImportPreview(BaseModel):
    """Preview of CSV import data"""
    headers: List[str]
    sample_rows: List[List[str]]
    total_rows: int
    column_mapping: Dict[str, str] = {}
    validation_errors: List[str] = []


class CSVImportMapping(BaseModel):
    """Column mapping for CSV import"""
    file_metadata_id: int
    column_mapping: Dict[str, str]  # csv_column -> model_field
    skip_errors: bool = False
    update_existing: bool = False


class FileProcessingProgress(BaseModel):
    """Real-time progress for file processing"""
    job_id: int
    job_type: str  # 'import' or 'export'
    progress_percent: int
    total_records: int
    processed_records: int
    failed_records: int
    status: str
    message: Optional[str] = None
    estimated_time_remaining: Optional[int] = None  # seconds
