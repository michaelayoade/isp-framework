# MinIO S3 File Storage Integration

## Overview

This module provides comprehensive file storage capabilities for the ISP Framework using MinIO S3-compatible storage. It supports file uploads/downloads with a 100MB max file size, customer CSV imports via background jobs, ticket media uploads, and secure, scalable file management.

## Features

- **File Upload/Download**: Support for files up to 100MB
- **Customer CSV Imports**: Automated background processing of customer data
- **Ticket Media**: Attach files to support tickets
- **Secure Storage**: S3-compatible storage with access controls
- **Background Processing**: Async file processing with job queues
- **Multi-bucket Support**: Separate buckets for different file types
- **File Validation**: MIME type checking and size limits
- **Metadata Storage**: Store additional file metadata
- **Expiration**: Automatic file cleanup with configurable expiration

## Architecture

### Storage Buckets

- `customer-uploads`: Customer-related files and documents
- `ticket-media`: Support ticket attachments and media
- `csv-imports`: Customer CSV import files
- `backups`: System backups and archives
- `temp`: Temporary files and processing

### Models

- **FileUpload**: Core file metadata and storage tracking
- **BackgroundJob**: Async job processing for CSV imports
- **CSVImport**: CSV import job tracking and validation

### Services

- **FileStorageService**: Core file operations (upload, download, delete)
- **CSVImportService**: Customer CSV import processing
- **BackgroundJobService**: Async job management

## Quick Start

### 1. Start MinIO Services

```bash
# Start MinIO with Docker
docker-compose -f docker-compose.full.yml up -d minio minio-setup

# Or use standalone MinIO
docker-compose -f docker-compose.minio.yml up -d
```

### 2. Access MinIO Console

- **Console**: http://localhost:9001
- **API**: http://localhost:9000
- **Credentials**: minioadmin / minioadmin123

### 3. Run Database Migration

```bash
alembic upgrade 20240723_create_file_storage
```

### 4. Test File Upload

```bash
# Get authentication token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Upload a file
curl -X POST http://localhost:8000/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.csv" \
  -F "file_type=csv" \
  -F "customer_id=1"
```

## API Endpoints

### File Management

#### Upload File
```http
POST /files/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

Parameters:
- file: The file to upload (max 100MB)
- file_type: Type of file (csv, image, document, etc.)
- customer_id: Optional customer ID
- ticket_id: Optional ticket ID
- service_id: Optional service ID
- metadata: JSON metadata object
- expires_at: Optional expiration date (ISO format)

Response:
{
  "id": 1,
  "filename": "customers.csv",
  "file_size": 1024,
  "mime_type": "text/csv",
  "file_type": "csv",
  "upload_status": "completed",
  "url": "http://localhost:9000/customer-uploads/customers.csv",
  "created_at": "2024-07-23T10:00:00Z"
}
```

#### Download File
```http
GET /files/download/{file_id}
Authorization: Bearer <token>

Response: File content with appropriate headers
```

#### List Customer Files
```http
GET /files/customer/{customer_id}
Authorization: Bearer <token>

Response: Array of file objects
```

#### Delete File
```http
DELETE /files/{file_id}
Authorization: Bearer <token>

Response: 204 No Content
```

### CSV Import

#### Start CSV Import
```http
POST /files/csv-import
Authorization: Bearer <token>
Content-Type: application/json

{
  "file_upload_id": 1,
  "import_type": "customers",
  "mapping_config": {
    "name": "full_name",
    "email": "email",
    "phone": "phone"
  },
  "validation_rules": {
    "email_required": true,
    "phone_format": "digits_only"
  }
}

Response:
{
  "job_id": "uuid-12345",
  "status": "pending",
  "created_at": "2024-07-23T10:00:00Z"
}
```

#### Check Job Status
```http
GET /files/jobs/{job_id}
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "job_type": "csv_import",
  "status": "completed",
  "total_rows": 100,
  "processed_rows": 100,
  "successful_rows": 95,
  "failed_rows": 5,
  "error_log": [...]
}
```

### Background Jobs

#### List Jobs
```http
GET /files/jobs
Authorization: Bearer <token>

Query Parameters:
- status: pending|processing|completed|failed
- job_type: csv_import|file_cleanup|...
- limit: Number of results to return
- offset: Pagination offset

Response: Array of job objects
```

## Configuration

### Environment Variables

```bash
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_USE_SSL=false

# Bucket Names
MINIO_BUCKET_CUSTOMER_UPLOADS=customer-uploads
MINIO_BUCKET_TICKET_MEDIA=ticket-media
MINIO_BUCKET_CSV_IMPORTS=csv-imports
MINIO_BUCKET_BACKUPS=backups
MINIO_BUCKET_TEMP=temp

# File Upload Limits
MAX_FILE_SIZE=104857600  # 100MB in bytes
ALLOWED_FILE_TYPES=csv,jpg,jpeg,png,pdf,doc,docx,xls,xlsx
```

### Docker Configuration

```yaml
# docker-compose.full.yml
services:
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"    # API
      - "9001:9001"    # Console
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
```

## Usage Examples

### Python Client

```python
import requests

# Upload customer CSV
with open('customers.csv', 'rb') as f:
    files = {'file': ('customers.csv', f, 'text/csv')}
    data = {
        'file_type': 'csv',
        'customer_id': 123,
        'metadata': json.dumps({'source': 'manual_upload'})
    }
    
    response = requests.post(
        'http://localhost:8000/files/upload',
        files=files,
        data=data,
        headers={'Authorization': f'Bearer {token}'}
    )

# Start CSV import
import_data = {
    'file_upload_id': response.json()['id'],
    'import_type': 'customers',
    'mapping_config': {
        'name': 'full_name',
        'email': 'email',
        'phone': 'phone'
    }
}

job_response = requests.post(
    'http://localhost:8000/files/csv-import',
    json=import_data,
    headers={'Authorization': f'Bearer {token}'}
)
```

### JavaScript Client

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('file_type', 'csv');
formData.append('customer_id', '123');

const response = await fetch('/files/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

// Check import status
const job = await response.json();
const statusResponse = await fetch(`/files/jobs/${job.job_id}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

## CSV Import Format

### Customer Import CSV

```csv
full_name,email,phone,address,city,state,postal_code,country,password
John Doe,john@example.com,1234567890,123 Main St,Anytown,CA,12345,USA,password123
Jane Smith,jane@example.com,0987654321,456 Oak Ave,Anytown,CA,12345,USA,password456
```

### CSV Import Rules

- **Required fields**: full_name, email
- **Email validation**: Must be valid email format
- **Phone validation**: Optional, digits only
- **Duplicate handling**: Skip duplicates based on email
- **Password generation**: Auto-generated if not provided

## Security

### Access Control

- **Authentication**: JWT-based authentication required
- **Authorization**: Role-based access control
- **File Access**: Files can only be accessed by authorized users
- **Customer Isolation**: Customers can only access their own files

### File Validation

- **Size Limits**: 100MB maximum per file
- **Type Validation**: MIME type checking
- **Content Scanning**: Basic virus scanning (optional)
- **Checksums**: MD5/SHA256 verification

## Monitoring

### Health Checks

```bash
# Check MinIO health
curl -f http://localhost:9000/minio/health/live

# Check API health
curl http://localhost:8000/health
```

### Metrics

- **Upload Success Rate**: Track successful vs failed uploads
- **Processing Time**: Average time for CSV imports
- **Storage Usage**: Monitor bucket usage
- **Error Rates**: Track validation and processing errors

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check MinIO is running: `docker ps`
   - Verify port 9000 is accessible
   - Check firewall settings

2. **Authentication Failed**
   - Verify JWT token is valid
   - Check user permissions
   - Ensure token hasn't expired

3. **Upload Size Limit**
   - Check `MAX_FILE_SIZE` environment variable
   - Verify nginx/client upload limits
   - Check MinIO bucket policies

4. **CSV Import Errors**
   - Verify CSV format matches expected schema
   - Check for special characters in data
   - Ensure required fields are present

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check logs
docker logs isp-backend
docker logs isp-minio
```

## Development

### Running Tests

```bash
# Run file storage tests
python test_file_storage.py

# Run pytest suite
pytest tests/test_file_storage.py -v
```

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start development services
docker-compose -f docker-compose.full.yml up -d

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

## Support

For issues and feature requests, please refer to the main ISP Framework documentation or create an issue in the project repository.
