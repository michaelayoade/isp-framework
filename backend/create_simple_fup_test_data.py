#!/usr/bin/env python3
"""
Simplified Test Data Creation Script for FUP Validation

This script creates minimal test data to validate the FUP reset functionality
by working around foreign key constraints and using existing data where possible.
"""

import sys
import os
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.insert(0, '/home/ispframework/projects/isp-framework/backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def create_simple_test_data():
    """Create simplified test data for FUP validation"""
    
    # Create database engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Creating simplified test data for FUP validation...")
        
        # First, let's check what reference data exists
        print("Checking existing reference data...")
        
        # Check locations
        locations_result = db.execute(text("SELECT id, name FROM locations LIMIT 1")).fetchone()
        location_id = locations_result[0] if locations_result else None
        
        # Check customer statuses
        status_result = db.execute(text("SELECT id, name FROM customer_statuses LIMIT 1")).fetchone()
        status_id = status_result[0] if status_result else None
        
        # Check service types
        service_type_result = db.execute(text("SELECT id, name FROM service_types LIMIT 1")).fetchone()
        service_type_id = service_type_result[0] if service_type_result else None
        
        print(f"Found location_id: {location_id}, status_id: {status_id}, service_type_id: {service_type_id}")
        
        # If we don't have required reference data, create it
        if not location_id:
            print("Creating default location...")
            db.execute(text("""
                INSERT INTO locations (name, address, city, country, created_at)
                VALUES ('Default Test Location', 'Test Address', 'Lagos', 'Nigeria', NOW())
                ON CONFLICT DO NOTHING
            """))
            db.commit()
            location_id = db.execute(text("SELECT id FROM locations WHERE name = 'Default Test Location'")).fetchone()[0]
        
        if not status_id:
            print("Creating default customer status...")
            db.execute(text("""
                INSERT INTO customer_statuses (code, name, description, is_active, created_at)
                VALUES ('active', 'Active', 'Active customer status', true, NOW())
                ON CONFLICT (code) DO NOTHING
            """))
            db.commit()
            status_id = db.execute(text("SELECT id FROM customer_statuses WHERE code = 'active'")).fetchone()[0]
        
        if not service_type_id:
            print("Creating default service type...")
            db.execute(text("""
                INSERT INTO service_types (code, name, description, is_active, created_at)
                VALUES ('internet', 'Internet Service', 'Internet connectivity service', true, NOW())
                ON CONFLICT (code) DO NOTHING
            """))
            db.commit()
            service_type_id = db.execute(text("SELECT id FROM service_types WHERE code = 'internet'")).fetchone()[0]
        
        # Now create the test customer
        print("Creating test customer...")
        customer_result = db.execute(text("""
            INSERT INTO customers (
                portal_id, name, email, phone, address, city, zip_code,
                status_id, location_id, category, date_add, created_at
            ) VALUES (
                'test_fup_customer_001',
                'Test Customer for FUP Validation',
                'test.fup@example.com',
                '+234-800-FUP-TEST',
                '123 FUP Test Street',
                'Lagos',
                '100001',
                :status_id,
                :location_id,
                'person',
                NOW(),
                NOW()
            )
            ON CONFLICT (portal_id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email
            RETURNING id
        """), {"status_id": status_id, "location_id": location_id})
        
        customer_id = customer_result.fetchone()[0]
        print(f"Created/updated test customer with ID: {customer_id}")
        
        # Create test customer service
        print("Creating test customer service...")
        service_result = db.execute(text("""
            INSERT INTO customer_services (
                customer_id, service_type_id, monthly_fee, activation_date,
                status, notes, created_at
            ) VALUES (
                :customer_id,
                :service_type_id,
                5000,
                NOW(),
                'active',
                'Test service for FUP validation',
                NOW()
            )
            ON CONFLICT DO NOTHING
            RETURNING id
        """), {"customer_id": customer_id, "service_type_id": service_type_id})
        
        service_row = service_result.fetchone()
        if service_row:
            service_id = service_row[0]
            print(f"Created test service with ID: {service_id}")
        else:
            # Service already exists, get its ID
            existing_service = db.execute(text("""
                SELECT id FROM customer_services WHERE customer_id = :customer_id LIMIT 1
            """), {"customer_id": customer_id}).fetchone()
            service_id = existing_service[0]
            print(f"Using existing test service with ID: {service_id}")
        
        # Create test internet service instance with FUP exceeded
        print("Creating test internet service instance...")
        db.execute(text("""
            INSERT INTO customer_internet_service_instances (
                customer_service_id, speed_download, speed_upload,
                fup_limit, fup_exceeded, fup_exceeded_date,
                original_speed_download, original_speed_upload, created_at
            ) VALUES (
                :service_id,
                10000,
                5000,
                50000000000,
                true,
                NOW(),
                10000,
                5000,
                NOW()
            )
            ON CONFLICT (customer_service_id) DO UPDATE SET
                fup_exceeded = true,
                fup_exceeded_date = NOW(),
                speed_download = 10000,
                speed_upload = 5000
        """), {"service_id": service_id})
        
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
    service_id = create_simple_test_data()
    print(f"\nTo test FUP reset, use:")
    print(f"curl -X POST http://localhost:8000/api/v1/services/internet/{service_id}/reset-fup")
