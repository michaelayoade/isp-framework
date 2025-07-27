"""
CSV Import Service for Customer Data Processing

Handles background processing of customer CSV imports with validation,
progress tracking, and error handling.
"""

import csv
import io
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from celery import current_task

from app.models.file_storage import ImportJob, ImportStatus, FileStatus
from app.models.customer import Customer
from app.repositories.file_storage_repository import ImportJobRepository, FileMetadataRepository
from app.repositories.customer import CustomerRepository
from app.services.file_storage_service import MinIOService
from app.core.database import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


class CustomerCSVImporter:
    """Service for processing customer CSV imports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.import_repo = ImportJobRepository(db)
        self.file_repo = FileMetadataRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.minio_service = MinIOService()
    
    def process_customer_csv_import(self, import_job_id: int) -> Dict[str, Any]:
        """Process customer CSV import job"""
        
        try:
            # Get import job
            import_job = self.import_repo.get_by_id(import_job_id)
            if not import_job:
                raise ValueError(f"Import job {import_job_id} not found")
            
            # Update job status
            self.import_repo.update_job_status(
                import_job_id,
                ImportStatus.PROCESSING,
                progress_percent=0
            )
            
            # Get file metadata
            file_record = self.file_repo.get_by_id(import_job.file_metadata_id)
            if not file_record:
                raise ValueError("File not found")
            
            # Download file from MinIO
            file_content = self._download_csv_file(file_record)
            
            # Parse and validate CSV
            csv_data = self._parse_csv(file_content)
            total_records = len(csv_data)
            
            # Update total records
            self.import_repo.update_job_status(
                import_job_id,
                ImportStatus.PROCESSING,
                total_records=total_records
            )
            
            # Process records
            processed_records = 0
            failed_records = 0
            validation_errors = []
            
            for index, row in enumerate(csv_data):
                try:
                    success = self._process_customer_row(row, import_job.import_config)
                    if success:
                        processed_records += 1
                    else:
                        failed_records += 1
                        
                except Exception as e:
                    failed_records += 1
                    validation_errors.append({
                        "row": index + 1,
                        "error": str(e),
                        "data": row
                    })
                    
                    if not import_job.import_config.get('skip_errors', False):
                        # Stop processing on first error if skip_errors is False
                        break
                
                # Update progress
                progress_percent = int((index + 1) / total_records * 100)
                self.import_repo.update_job_status(
                    import_job_id,
                    ImportStatus.PROCESSING,
                    progress_percent=progress_percent,
                    processed_records=processed_records,
                    failed_records=failed_records
                )
                
                # Update Celery task progress
                if current_task:
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'current': index + 1,
                            'total': total_records,
                            'percent': progress_percent
                        }
                    )
            
            # Final status update
            final_status = ImportStatus.COMPLETED if failed_records == 0 else ImportStatus.FAILED
            if failed_records > 0 and import_job.import_config.get('skip_errors', True):
                final_status = ImportStatus.COMPLETED
            
            self.import_repo.update_job_status(
                import_job_id,
                final_status,
                progress_percent=100,
                processed_records=processed_records,
                failed_records=failed_records,
                error_message=validation_errors[0]['error'] if validation_errors else None
            )
            
            # Update file status
            self.file_repo.update_file_status(
                file_record.id,
                FileStatus.PROCESSED if final_status == ImportStatus.COMPLETED else FileStatus.FAILED
            )
            
            return {
                "status": final_status.value,
                "total_records": total_records,
                "processed_records": processed_records,
                "failed_records": failed_records,
                "validation_errors": validation_errors
            }
            
        except Exception as e:
            logger.error(f"Error processing customer CSV import: {e}")
            
            # Update job with error
            self.import_repo.update_job_status(
                import_job_id,
                ImportStatus.FAILED,
                error_message=str(e)
            )
            
            # Update file status
            file_record = self.file_repo.get_by_id(
                self.import_repo.get_by_id(import_job_id).file_metadata_id
            )
            if file_record:
                self.file_repo.update_file_status(file_record.id, FileStatus.FAILED)
            
            raise
    
    def _download_csv_file(self, file_record) -> str:
        """Download CSV file from MinIO"""
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
            self.minio_service.download_file(
                file_record.bucket_name,
                file_record.object_key,
                temp_file.name
            )
            
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import os
            os.unlink(temp_file.name)
            
            return content
    
    def _parse_csv(self, file_content: str) -> List[Dict[str, str]]:
        """Parse CSV content into list of dictionaries"""
        
        csv_reader = csv.DictReader(io.StringIO(file_content))
        return list(csv_reader)
    
    def _process_customer_row(self, row: Dict[str, str], config: Dict[str, Any]) -> bool:
        """Process individual customer row"""
        
        # Required fields mapping
        field_mapping = {
            'first_name': ['first_name', 'firstname', 'first name'],
            'last_name': ['last_name', 'lastname', 'last name'],
            'email': ['email', 'email_address', 'email address'],
            'phone': ['phone', 'phone_number', 'phone number', 'mobile'],
            'address': ['address', 'street_address', 'street address'],
            'city': ['city', 'town'],
            'postal_code': ['postal_code', 'postalcode', 'zip', 'zip_code'],
            'portal_id': ['portal_id', 'portalid', 'customer_id', 'customerid']
        }
        
        # Map CSV columns to model fields
        customer_data = {}
        for model_field, csv_fields in field_mapping.items():
            for csv_field in csv_fields:
                if csv_field in row and row[csv_field].strip():
                    customer_data[model_field] = row[csv_field].strip()
                    break
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if field not in customer_data or not customer_data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Check if customer exists
        existing_customer = self.customer_repo.get_by_email(customer_data['email'])
        
        if existing_customer:
            if config.get('update_existing', False):
                # Update existing customer
                for key, value in customer_data.items():
                    setattr(existing_customer, key, value)
                self.db.commit()
                return True
            else:
                # Skip existing customer
                return False
        
        # Create new customer
        new_customer = Customer(
            first_name=customer_data['first_name'],
            last_name=customer_data['last_name'],
            email=customer_data['email'],
            phone=customer_data.get('phone'),
            address=customer_data.get('address'),
            city=customer_data.get('city'),
            postal_code=customer_data.get('postal_code'),
            status="active"
        )
        
        self.customer_repo.create(new_customer)
        return True
    
    def get_csv_preview(self, file_metadata_id: int) -> Dict[str, Any]:
        """Get preview of CSV file for mapping"""
        
        file_record = self.file_repo.get_by_id(file_metadata_id)
        if not file_record:
            raise ValueError("File not found")
        
        file_content = self._download_csv_file(file_record)
        csv_data = self._parse_csv(file_content)
        
        if not csv_data:
            return {
                "headers": [],
                "sample_rows": [],
                "total_rows": 0,
                "validation_errors": ["Empty CSV file"]
            }
        
        headers = list(csv_data[0].keys())
        sample_rows = [list(row.values()) for row in csv_data[:5]]
        
        return {
            "headers": headers,
            "sample_rows": sample_rows,
            "total_rows": len(csv_data),
            "validation_errors": []
        }


# Celery task for background processing
def process_customer_csv_import_task(import_job_id: int) -> Dict[str, Any]:
    """Celery task for processing customer CSV imports"""
    
    db = SessionLocal()
    try:
        importer = CustomerCSVImporter(db)
        return importer.process_customer_csv_import(import_job_id)
    finally:
        db.close()
