#!/usr/bin/env python3
"""
Test Data Creation Script for FUP Validation

This script creates the necessary test data to validate the FUP reset functionality
by directly inserting records into the database using SQLAlchemy models.
"""

import sys
import os
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.insert(0, '/home/ispframework/projects/isp-framework/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import Customer, CustomerService, CustomerInternetService

def create_test_data():
    """Create test data for FUP validation"""
    
    # Create database engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Creating test data for FUP validation...")
        
        # 1. Create test customer
        test_customer = Customer(
            portal_id="test_fup_customer_001",
            name="Test Customer for FUP Validation",
            email="test.fup@example.com",
            phone="+234-800-FUP-TEST",
            address="123 FUP Test Street, Lagos",
            city="Lagos",
            zip_code="100001",
            status_id=1,  # Assuming active status
            location_id=1,  # Assuming default location
            category="person",
            date_add=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        
        # Check if customer already exists
        existing_customer = db.query(Customer).filter(
            Customer.portal_id == "test_fup_customer_001"
        ).first()
        
        if existing_customer:
            print(f"Test customer already exists with ID: {existing_customer.id}")
            customer_id = existing_customer.id
        else:
            db.add(test_customer)
            db.flush()  # Get the ID without committing
            customer_id = test_customer.id
            print(f"Created test customer with ID: {customer_id}")
        
        # 2. Create test customer service
        test_service = CustomerService(
            customer_id=customer_id,
            service_type_id=1,  # Assuming internet service type
            monthly_fee=5000,  # 50.00 in cents
            activation_date=datetime.now(timezone.utc),
            status="active",
            notes="Test service for FUP validation",
            created_at=datetime.now(timezone.utc)
        )
        
        # Check if service already exists
        existing_service = db.query(CustomerService).filter(
            CustomerService.customer_id == customer_id
        ).first()
        
        if existing_service:
            print(f"Test service already exists with ID: {existing_service.id}")
            service_id = existing_service.id
        else:
            db.add(test_service)
            db.flush()  # Get the ID without committing
            service_id = test_service.id
            print(f"Created test service with ID: {service_id}")
        
        # 3. Create test internet service instance with FUP exceeded
        test_internet_service = CustomerInternetService(
            customer_service_id=service_id,
            speed_download=10000,  # 10 Mbps
            speed_upload=5000,     # 5 Mbps
            fup_limit=50000000000,  # 50 GB in bytes
            fup_exceeded=True,      # Set to True for testing FUP reset
            fup_exceeded_date=datetime.now(timezone.utc),
            original_speed_download=10000,
            original_speed_upload=5000,
            created_at=datetime.now(timezone.utc)
        )
        
        # Check if internet service already exists
        existing_internet_service = db.query(CustomerInternetService).filter(
            CustomerInternetService.customer_service_id == service_id
        ).first()
        
        if existing_internet_service:
            print(f"Test internet service already exists for service ID: {service_id}")
            # Update FUP status for testing
            existing_internet_service.fup_exceeded = True
            existing_internet_service.fup_exceeded_date = datetime.now(timezone.utc)
            print("Updated existing internet service to FUP exceeded status")
        else:
            db.add(test_internet_service)
            print(f"Created test internet service for service ID: {service_id}")
        
        # Commit all changes
        db.commit()
        
        print("\n=== TEST DATA CREATION SUMMARY ===")
        print(f"Customer ID: {customer_id}")
        print(f"Service ID: {service_id}")
        print(f"Internet Service: FUP exceeded = True")
        print(f"FUP Limit: 50 GB")
        print(f"Speed: 10 Mbps down / 5 Mbps up")
        print("\nTest data created successfully!")
        print(f"You can now test FUP reset with service ID: {service_id}")
        
        return service_id
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    service_id = create_test_data()
    print(f"\nTo test FUP reset, use: curl -X POST http://localhost:8000/api/v1/services/internet/{service_id}/reset-fup")
