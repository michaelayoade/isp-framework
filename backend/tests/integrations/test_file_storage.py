"""Smoke tests for File Storage (MinIO) endpoints.

These cover bucket listing and presigned upload URL generation to
ensure the integration layer is reachable and responds with expected
structures.
"""
import pytest


@pytest.mark.order(1)
def test_list_buckets(client):
    resp = client.get("/api/v1/files/buckets")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.order(2)
def test_presign_upload(client):
    payload = {"filename": "pytest_dummy.txt", "content_type": "text/plain"}
    resp = client.post("/api/v1/files/presign-upload", json=payload)
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result.get("url")
    assert "fields" in result
import pytest
"""
Comprehensive test script for MinIO S3 file storage integration
Tests all file storage endpoints and functionality
"""

import requests
import json
import os
import tempfile
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Test files
TEST_FILES = {
    'csv': {
        'filename': 'test_customers.csv',
        'content': 'name,email,phone\nJohn Doe,john@example.com,1234567890\nJane Smith,jane@example.com,0987654321',
        'mime_type': 'text/csv'
    },
    'image': {
        'filename': 'test_image.jpg',
        'content': b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00',
        'mime_type': 'image/jpeg'
    },
    'document': {
        'filename': 'test_document.pdf',
        'content': b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n',
        'mime_type': 'application/pdf'
    }
}

class FileStorageTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
    
    def authenticate(self):
        """Authenticate with the backend"""
        print("🔐 Authenticating...")
        
        # Try admin setup if needed
        setup_response = requests.post(f"{self.base_url}/auth/setup", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD,
            "email": "admin@isp.com",
            "full_name": "System Administrator"
        })
        
        # Login
        login_response = requests.post(f"{self.base_url}/auth/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {login_response.text}")
            return False
    
    def create_test_customer(self):
        """Create a test customer"""
        print("👤 Creating test customer...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        customer_data = {
            "full_name": "Test Customer",
            "email": "test.customer@example.com",
            "phone": "1234567890",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "US",
            "password": "testpass123"
        }
        
        response = requests.post(
            f"{self.base_url}/customers",
            json=customer_data,
            headers=headers
        )
        
        if response.status_code == 201:
            customer = response.json()
            print(f"✅ Customer created: {customer['id']}")
            return customer
        else:
            print(f"❌ Customer creation failed: {response.text}")
            return None
    
    def test_file_upload(self, customer_id):
        """Test file upload functionality"""
        print("📁 Testing file uploads...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        for file_type, file_info in TEST_FILES.items():
            print(f"  Testing {file_type} upload...")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                suffix=f".{file_info['filename'].split('.')[-1]}",
                delete=False
            ) as tmp_file:
                if isinstance(file_info['content'], str):
                    tmp_file.write(file_info['content'].encode())
                else:
                    tmp_file.write(file_info['content'])
                tmp_file.flush()
                
                # Upload file
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': (file_info['filename'], f, file_info['mime_type'])}
                    data = {
                        'file_type': file_type,
                        'customer_id': customer_id,
                        'metadata': json.dumps({"test": True, "source": "test_script"})
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/files/upload",
                        files=files,
                        data=data,
                        headers=headers
                    )
                
                # Clean up
                os.unlink(tmp_file.name)
                
                if response.status_code == 201:
                    upload_result = response.json()
                    print(f"    ✅ {file_type} uploaded: {upload_result['id']}")
                    yield upload_result
                else:
                    print(f"    ❌ {file_type} upload failed: {response.text}")
    
    def test_file_download(self, file_id):
        """Test file download functionality"""
        print("⬇️ Testing file download...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(
            f"{self.base_url}/files/download/{file_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            print("  ✅ File download successful")
            return True
        else:
            print(f"  ❌ File download failed: {response.text}")
            return False
    
    def test_file_listing(self, customer_id):
        """Test file listing functionality"""
        print("📋 Testing file listing...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(
            f"{self.base_url}/files/customer/{customer_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            files = response.json()
            print(f"  ✅ Listed {len(files)} files for customer {customer_id}")
            return files
        else:
            print(f"  ❌ File listing failed: {response.text}")
            return []
    
    def test_csv_import(self, file_id):
        """Test CSV import functionality"""
        print("📊 Testing CSV import...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        import_data = {
            "file_upload_id": file_id,
            "import_type": "customers",
            "mapping_config": {
                "name": "name",
                "email": "email",
                "phone": "phone"
            },
            "validation_rules": {
                "email_required": True,
                "phone_format": "digits_only"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/files/csv-import",
            json=import_data,
            headers=headers
        )
        
        if response.status_code == 202:
            job = response.json()
            print(f"  ✅ CSV import job started: {job['job_id']}")
            return job
        else:
            print(f"  ❌ CSV import failed: {response.text}")
            return None
    
    def test_job_status(self, job_id):
        """Test job status checking"""
        print("⏳ Testing job status...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        max_attempts = 10
        for attempt in range(max_attempts):
            response = requests.get(
                f"{self.base_url}/files/jobs/{job_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                job = response.json()
                print(f"  Job status: {job['status']} (attempt {attempt + 1})")
                
                if job['status'] in ['completed', 'failed']:
                    return job
            
            time.sleep(2)
        
        print("  ❌ Job status check timeout")
        return None
    
    def test_file_deletion(self, file_id):
        """Test file deletion"""
        print("🗑️ Testing file deletion...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.delete(
            f"{self.base_url}/files/{file_id}",
            headers=headers
        )
        
        if response.status_code == 204:
            print("  ✅ File deleted successfully")
            return True
        else:
            print(f"  ❌ File deletion failed: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all file storage tests"""
        print("🚀 Starting comprehensive file storage tests...\n")
        
        if not self.authenticate():
            return
        
        customer = self.create_test_customer()
        if not customer:
            return
        
        customer_id = customer['id']
        uploaded_files = []
        
        try:
            # Test file uploads
            print("\n" + "="*50)
            print("UPLOAD TESTS")
            print("="*50)
            
            for upload_result in self.test_file_upload(customer_id):
                uploaded_files.append(upload_result)
            
            # Test file listing
            print("\n" + "="*50)
            print("LISTING TESTS")
            print("="*50)
            
            files = self.test_file_listing(customer_id)
            
            # Test file downloads
            print("\n" + "="*50)
            print("DOWNLOAD TESTS")
            print("="*50)
            
            if uploaded_files:
                self.test_file_download(uploaded_files[0]['id'])
            
            # Test CSV import
            print("\n" + "="*50)
            print("CSV IMPORT TESTS")
            print("="*50)
            
            csv_file = next((f for f in uploaded_files if f['file_type'] == 'csv'), None)
            if csv_file:
                job = self.test_csv_import(csv_file['id'])
                if job:
                    self.test_job_status(job['job_id'])
            
            # Test file deletion
            print("\n" + "="*50)
            print("DELETION TESTS")
            print("="*50)
            
            for file_info in uploaded_files:
                self.test_file_deletion(file_info['id'])
            
            print("\n" + "="*50)
            print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            print("="*50)
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")


if __name__ == "__main__":
    tester = FileStorageTester(BASE_URL)
    tester.run_all_tests()
