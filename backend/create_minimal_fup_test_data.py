#!/usr/bin/env python3
"""
Minimal Test Data Creation Script for FUP Validation

This script creates minimal test data using the actual database schema
to validate the FUP reset functionality.
"""

import sys
import os
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.insert(0, '/home/ispframework/projects/isp-framework/backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def create_minimal_test_data():
    """Create minimal test data for FUP validation using actual schema"""
    
    # Create database engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Creating minimal test data for FUP validation...")
        
        # Create a default location if none exists
        print("Creating default location...")
        db.execute(text("""
            INSERT INTO locations (name, code, description, country, city, is_active, created_at)
            VALUES ('Test Location', 'TEST_LOC', 'Test location for FUP validation', 'Nigeria', 'Lagos', true, NOW())
            ON CONFLICT (code) DO NOTHING
        """))
        db.commit()
        
        # Get the location ID
        location_result = db.execute(text("SELECT id FROM locations WHERE code = 'TEST_LOC'")).fetchone()
        location_id = location_result[0]
        print(f"Using location ID: {location_id}")
        
        # Get existing customer status and service type IDs
        status_result = db.execute(text("SELECT id FROM customer_statuses LIMIT 1")).fetchone()
        status_id = status_result[0] if status_result else 1
        
        service_type_result = db.execute(text("SELECT id FROM service_types LIMIT 1")).fetchone()
        service_type_id = service_type_result[0] if service_type_result else 1
        
        print(f"Using status_id: {status_id}, service_type_id: {service_type_id}")
        
        # Create test customer with minimal required fields
        print("Creating test customer...")
        customer_result = db.execute(text("""
            INSERT INTO customers (
                portal_id, name, email, status_id, location_id, 
                category, date_add, created_at
            ) VALUES (
                'test_fup_customer_minimal',
                'Test Customer FUP',
                'test.fup.minimal@example.com',
                :status_id,
                :location_id,
                'person',
                NOW(),
                NOW()
            )
            ON CONFLICT (portal_id) DO UPDATE SET
                name = EXCLUDED.name
            RETURNING id
        """), {"status_id": status_id, "location_id": location_id})
        
        customer_id = customer_result.fetchone()[0]
        print(f"Created/updated test customer with ID: {customer_id}")
        
        # Create test customer service
        print("Creating test customer service...")
        service_result = db.execute(text("""
            INSERT INTO customer_services (
                customer_id, service_type_id, monthly_fee, 
                activation_date, status, created_at
            ) VALUES (
                :customer_id,
                :service_type_id,
                5000,
                NOW(),
                'active',
                NOW()
            )
            RETURNING id
        """), {"customer_id": customer_id, "service_type_id": service_type_id})
        
        service_id = service_result.fetchone()[0]
        print(f"Created test service with ID: {service_id}")
        
        # Create test internet service instance with FUP exceeded
        print("Creating test internet service instance...")
        db.execute(text("""
            INSERT INTO customer_internet_service_instances (
                customer_service_id, speed_download, speed_upload,
                fup_limit, fup_exceeded, fup_exceeded_date, created_at
            ) VALUES (
                :service_id,
                10000,
                5000,
                50000000000,
                true,
                NOW(),
                NOW()
            )
            ON CONFLICT (customer_service_id) DO UPDATE SET
                fup_exceeded = true,
                fup_exceeded_date = NOW()
        """), {"service_id": service_id})
        
        db.commit()
        
        print("\n=== MINIMAL TEST DATA CREATION SUMMARY ===")
        print(f"✅ Customer ID: {customer_id}")
        print(f"✅ Service ID: {service_id}")
        print(f"✅ Internet Service: FUP exceeded = True")
        print(f"✅ FUP Limit: 50 GB")
        print(f"✅ Speed: 10 Mbps down / 5 Mbps up")
        print("\n🎯 Test data created successfully!")
        print(f"🚀 Ready to test FUP reset with service ID: {service_id}")
        
        return service_id
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    service_id = create_minimal_test_data()
    print(f"\n📋 To test FUP reset, use:")
    print(f"curl -X POST 'http://localhost:8000/api/v1/services/internet/{service_id}/reset-fup' \\")
    print(f"  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"  -H 'Content-Type: application/json'")
