#!/usr/bin/env python3
"""
Working Test Data Creation Script for FUP Validation

This script creates test data using the actual database schema
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

def create_working_test_data():
    """Create working test data for FUP validation using actual schema"""
    
    # Create database engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Creating working test data for FUP validation...")
        
        # Get the location ID we created earlier
        location_result = db.execute(text("SELECT id FROM locations WHERE code = 'TEST_LOC'")).fetchone()
        location_id = location_result[0] if location_result else 1
        print(f"Using location ID: {location_id}")
        
        # Get existing customer status ID
        status_result = db.execute(text("SELECT id FROM customer_statuses LIMIT 1")).fetchone()
        status_id = status_result[0] if status_result else 1
        
        # Get existing service template ID (if any)
        template_result = db.execute(text("SELECT id FROM service_templates LIMIT 1")).fetchone()
        template_id = template_result[0] if template_result else None
        
        print(f"Using status_id: {status_id}, template_id: {template_id}")
        
        # Get existing customer ID or use the one we created
        customer_result = db.execute(text("SELECT id FROM customers WHERE portal_id = 'test_fup_customer_minimal'")).fetchone()
        customer_id = customer_result[0] if customer_result else 2
        print(f"Using customer ID: {customer_id}")
        
        # Create test customer service with actual schema
        print("Creating test customer service...")
        service_result = db.execute(text("""
            INSERT INTO customer_services (
                customer_id, service_template_id, service_number, display_name,
                status, activation_date, created_at
            ) VALUES (
                :customer_id,
                :template_id,
                'TEST-FUP-001',
                'Test FUP Service',
                'active',
                NOW(),
                NOW()
            )
            RETURNING id
        """), {"customer_id": customer_id, "template_id": template_id})
        
        service_id = service_result.fetchone()[0]
        print(f"Created test service with ID: {service_id}")
        
        # Create test internet service instance with actual schema
        print("Creating test internet service instance...")
        db.execute(text("""
            INSERT INTO customer_internet_service_instances (
                customer_service_id, download_speed_kbps, upload_speed_kbps,
                current_speed_down_kbps, current_speed_up_kbps,
                fup_exceeded, monthly_usage_gb, created_at
            ) VALUES (
                :service_id,
                10000,
                5000,
                10000,
                5000,
                true,
                55.0,
                NOW()
            )
            ON CONFLICT (customer_service_id) DO UPDATE SET
                fup_exceeded = true,
                monthly_usage_gb = 55.0,
                download_speed_kbps = 10000,
                upload_speed_kbps = 5000
        """), {"service_id": service_id})
        
        db.commit()
        
        print("\n=== WORKING TEST DATA CREATION SUMMARY ===")
        print(f"✅ Customer ID: {customer_id}")
        print(f"✅ Service ID: {service_id}")
        print(f"✅ Internet Service: FUP exceeded = True")
        print(f"✅ Monthly Usage: 55 GB (over limit)")
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
    service_id = create_working_test_data()
    print(f"\n📋 To test FUP reset, use:")
    print(f"curl -X POST 'http://localhost:8000/api/v1/services/internet/{service_id}/reset-fup' \\")
    print(f"  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"  -H 'Content-Type: application/json'")
