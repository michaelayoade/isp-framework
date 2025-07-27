"""
File Storage Service for MinIO S3 Integration

Handles MinIO S3 operations, file uploads/downloads, presigned URLs,
and bucket management for ISP Framework file storage.
"""

import os
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from minio import Minio
from minio.error import S3Error
import logging

from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.file_storage import FileMetadata, FileCategory, FileStatus
from app.repositories.file_storage_repository import FileMetadataRepository

logger = logging.getLogger(__name__)


class MinIOService:
    """Service for MinIO S3 operations"""
    
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.buckets = {
            'customers': 'isp-customers',
            'tickets': 'isp-tickets',
            'imports': 'isp-imports',
            'exports': 'isp-exports',
            'backups': 'isp-backups',
            'temp': 'isp-temp'
        }
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Ensure all required buckets exist"""
        for bucket_name in self.buckets.values():
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    logger.info(f"Created bucket: {bucket_name}")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket_name}: {e}")
                raise
    
    def get_bucket_for_category(self, category: FileCategory) -> str:
        """Get appropriate bucket for file category"""
        mapping = {
            FileCategory.CUSTOMER_DOCUMENT: self.buckets['customers'],
            FileCategory.TICKET_ATTACHMENT: self.buckets['tickets'],
            FileCategory.CUSTOMER_IMPORT: self.buckets['imports'],
            FileCategory.SERVICE_EXPORT: self.buckets['exports'],
            FileCategory.CONFIG_BACKUP: self.buckets['backups'],
            FileCategory.SYSTEM_FILE: self.buckets['temp']
        }
        return mapping.get(category, self.buckets['temp'])
    
    def generate_presigned_upload_url(
        self,
        filename: str,
        file_size: int,
        mime_type: str,
        category: FileCategory,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """Generate presigned URL for file upload"""
        try:
            bucket_name = self.get_bucket_for_category(category)
            object_key = self._generate_object_key(filename, category)
            
            # Generate presigned URL for PUT operation
            presigned_url = self.client.presigned_put_object(
                bucket_name,
                object_key,
                expires=timedelta(seconds=expires_in)
            )
            
            return {
                "presigned_url": presigned_url,
                "bucket_name": bucket_name,
                "object_key": object_key,
                "expires_in": expires_in,
                "expires_at": datetime.utcnow() + timedelta(seconds=expires_in)
            }
            
        except S3Error as e:
            logger.error(f"Error generating presigned upload URL: {e}")
            raise
    
    def generate_presigned_download_url(
        self,
        bucket_name: str,
        object_key: str,
        filename: str,
        expires_in: int = 3600
    ) -> str:
        """Generate presigned URL for file download"""
        try:
            return self.client.presigned_get_object(
                bucket_name,
                object_key,
                expires=timedelta(seconds=expires_in),
                response_headers={
                    'response-content-disposition': f'attachment; filename="{filename}"'
                }
            )
        except S3Error as e:
            logger.error(f"Error generating presigned download URL: {e}")
            raise
    
    def upload_file(
        self,
        file_path: str,
        bucket_name: str,
        object_key: str,
        content_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """Upload file to MinIO"""
        try:
            file_size = os.path.getsize(file_path)
            
            # Calculate checksum
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Upload file
            self.client.fput_object(
                bucket_name,
                object_key,
                file_path,
                content_type=content_type
            )
            
            return {
                "bucket_name": bucket_name,
                "object_key": object_key,
                "file_size": file_size,
                "checksum": file_hash,
                "etag": self._get_etag(bucket_name, object_key)
            }
            
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def download_file(
        self,
        bucket_name: str,
        object_key: str,
        file_path: str
    ) -> bool:
        """Download file from MinIO"""
        try:
            self.client.fget_object(bucket_name, object_key, file_path)
            return True
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            return False
    
    def delete_file(self, bucket_name: str, object_key: str) -> bool:
        """Delete file from MinIO"""
        try:
            self.client.remove_object(bucket_name, object_key)
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def get_file_info(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """Get file information from MinIO"""
        try:
            stat = self.client.stat_object(bucket_name, object_key)
            return {
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata
            }
        except S3Error as e:
            logger.error(f"Error getting file info: {e}")
            raise
    
    def list_files(
        self,
        bucket_name: str,
        prefix: str = "",
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """List files in bucket"""
        try:
            objects = self.client.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            
            return [
                {
                    "object_name": obj.object_name,
                    "size": obj.size,
                    "etag": obj.etag,
                    "last_modified": obj.last_modified,
                    "content_type": obj.content_type
                }
                for obj in objects
            ]
            
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    def _generate_object_key(self, filename: str, category: FileCategory) -> str:
        """Generate unique object key for file"""
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        return f"{timestamp}/{category.value}/{unique_id}_{safe_filename}"
    
    def _get_etag(self, bucket_name: str, object_key: str) -> str:
        """Get ETag for uploaded file"""
        try:
            stat = self.client.stat_object(bucket_name, object_key)
            return stat.etag
        except S3Error:
            return ""


class FileStorageService:
    """High-level file storage service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.minio_service = MinIOService()
        self.file_repo = FileMetadataRepository(db)
    
    async def upload_file(
        self,
        filename: str,
        file_size: int,
        mime_type: str,
        category: FileCategory,
        uploaded_by: int,
        customer_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Initiate file upload and create metadata"""
        
        # Validate file size
        if file_size > 104857600:  # 100MB
            raise ValueError("File size exceeds 100MB limit")
        
        # Generate presigned upload URL
        upload_info = self.minio_service.generate_presigned_upload_url(
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            category=category
        )
        
        # Create file metadata record
        file_record = self.file_repo.create_file_metadata(
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            category=category,
            uploaded_by=uploaded_by,
            customer_id=customer_id,
            ticket_id=ticket_id,
            bucket_name=upload_info["bucket_name"],
            object_key=upload_info["object_key"],
            metadata=metadata or {}
        )
        
        return {
            "file_id": file_record.id,
            "upload_url": upload_info["presigned_url"],
            "expires_at": upload_info["expires_at"],
            "bucket_name": upload_info["bucket_name"],
            "object_key": upload_info["object_key"]
        }
    
    async def get_download_url(
        self,
        file_id: int,
        expires_in: int = 3600
    ) -> str:
        """Get presigned download URL for file"""
        
        file_record = self.file_repo.get_by_id(file_id)
        if not file_record:
            raise ValueError("File not found")
        
        return self.minio_service.generate_presigned_download_url(
            bucket_name=file_record.bucket_name,
            object_key=file_record.object_key,
            filename=file_record.filename,
            expires_in=expires_in
        )
    
    async def delete_file(self, file_id: int) -> bool:
        """Delete file and metadata"""
        
        file_record = self.file_repo.get_by_id(file_id)
        if not file_record:
            return False
        
        # Delete from MinIO
        success = self.minio_service.delete_file(
            file_record.bucket_name,
            file_record.object_key
        )
        
        if success:
            # Delete metadata
            self.file_repo.delete_file_metadata(file_id)
            
        return success
    
    def get_file_info(self, file_id: int) -> Dict[str, Any]:
        """Get detailed file information"""
        
        file_record = self.file_repo.get_by_id(file_id)
        if not file_record:
            raise ValueError("File not found")
        
        # Get MinIO file info
        minio_info = self.minio_service.get_file_info(
            file_record.bucket_name,
            file_record.object_key
        )
        
        return {
            "metadata": file_record,
            "storage_info": minio_info
        }
