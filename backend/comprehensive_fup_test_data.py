#!/usr/bin/env python3
"""
Comprehensive FUP Test Data Seeding Solution

This script creates all necessary reference data and test instances
to enable complete FUP reset validation and end-to-end testing.
"""
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append('/app')

from app.core.config import settings

def create_comprehensive_fup_test_data():
    """Create comprehensive test data for FUP validation"""
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            print("🚀 Starting Comprehensive FUP Test Data Creation...")
            
            # Step 1: Create Location (required for customers)
            print("\n1️⃣ Creating test location...")
            location_result = session.execute(text("""
                INSERT INTO locations (name, type, address, city, state_province, postal_code, country, is_active)
                VALUES ('Test Location', 'office', '123 Test St', 'Test City', 'Test State', '12345', 'US', true)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id;
            """))
            location_id = location_result.fetchone()[0]
            print(f"✅ Location created with ID: {location_id}")
            
            # Step 2: Create Customer Status (if not exists)
            print("\n2️⃣ Creating customer status...")
            status_result = session.execute(text("""
                INSERT INTO customer_statuses (code, name, description, is_active, is_system)
                VALUES ('ACTIVE', 'Active', 'Active customer status', true, true)
                ON CONFLICT (code) DO UPDATE SET code = EXCLUDED.code
                RETURNING id;
            """))
            customer_status_id = status_result.fetchone()[0]
            print(f"✅ Customer status created with ID: {customer_status_id}")
            
            # Step 3: Create Service Type (if not exists)
            print("\n3️⃣ Creating service type...")
            service_type_result = session.execute(text("""
                INSERT INTO service_types (code, name, description, is_active, is_system)
                VALUES ('INTERNET', 'Internet Service', 'High-speed internet service', true, true)
                ON CONFLICT (code) DO UPDATE SET code = EXCLUDED.code
                RETURNING id;
            """))
            service_type_id = service_type_result.fetchone()[0]
            print(f"✅ Service type created with ID: {service_type_id}")
            
            # Step 4: Create Service Template (required for customer_services)
            print("\n4️⃣ Creating service template...")
            template_result = session.execute(text("""
                INSERT INTO service_templates (
                    name, description, service_type_id, base_price, setup_fee, 
                    billing_cycle, is_active, created_at, updated_at
                )
                VALUES (
                    'Basic Internet 100Mbps', 
                    'Basic internet service with 100Mbps speed and 500GB FUP',
                    :service_type_id,
                    49.99,
                    25.00,
                    'monthly',
                    true,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id;
            """), {"service_type_id": service_type_id})
            template_id = template_result.fetchone()[0]
            print(f"✅ Service template created with ID: {template_id}")
            
            # Step 5: Create Test Customer
            print("\n5️⃣ Creating test customer...")
            customer_result = session.execute(text("""
                INSERT INTO customers (
                    name, email, phone, address, city, state_province, 
                    postal_code, country, customer_status_id, location_id,
                    is_active, created_at, updated_at
                )
                VALUES (
                    'FUP Test Customer',
                    'fup.test@example.com',
                    '+1-555-FUP-TEST',
                    '456 FUP Test Ave',
                    'Test City',
                    'Test State',
                    '12345',
                    'US',
                    :customer_status_id,
                    :location_id,
                    true,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id;
            """), {
                "customer_status_id": customer_status_id,
                "location_id": location_id
            })
            customer_id = customer_result.fetchone()[0]
            print(f"✅ Customer created with ID: {customer_id}")
            
            # Step 6: Create Customer Service
            print("\n6️⃣ Creating customer service...")
            service_result = session.execute(text("""
                INSERT INTO customer_services (
                    customer_id, service_template_id, service_type_id,
                    status, start_date, monthly_fee, setup_fee,
                    is_active, created_at, updated_at
                )
                VALUES (
                    :customer_id,
                    :service_template_id,
                    :service_type_id,
                    'ACTIVE',
                    CURRENT_DATE,
                    49.99,
                    25.00,
                    true,
                    NOW(),
                    NOW()
                )
                RETURNING id;
            """), {
                "customer_id": customer_id,
                "service_template_id": template_id,
                "service_type_id": service_type_id
            })
            service_id = service_result.fetchone()[0]
            print(f"✅ Customer service created with ID: {service_id}")
            
            # Step 7: Create Customer Internet Service (for FUP testing)
            print("\n7️⃣ Creating customer internet service with FUP data...")
            internet_service_result = session.execute(text("""
                INSERT INTO customer_internet_services (
                    customer_service_id, download_speed_mbps, upload_speed_mbps,
                    data_limit_gb, fup_threshold_gb, fup_speed_mbps,
                    current_usage_gb, fup_reset_date, is_fup_active,
                    created_at, updated_at
                )
                VALUES (
                    :customer_service_id,
                    100,  -- 100 Mbps download
                    20,   -- 20 Mbps upload
                    500,  -- 500 GB monthly limit
                    400,  -- FUP kicks in at 400 GB
                    10,   -- FUP speed reduced to 10 Mbps
                    450,  -- Current usage 450 GB (over FUP threshold)
                    :fup_reset_date,
                    true, -- FUP is currently active
                    NOW(),
                    NOW()
                )
                RETURNING customer_service_id;
            """), {
                "customer_service_id": service_id,
                "fup_reset_date": (datetime.now() + timedelta(days=15)).date()
            })
            internet_service_id = internet_service_result.fetchone()[0]
            print(f"✅ Internet service created with service ID: {internet_service_id}")
            print(f"   📊 Current usage: 450 GB (over 400 GB FUP threshold)")
            print(f"   🔴 FUP Status: ACTIVE (speed limited to 10 Mbps)")
            
            # Step 8: Commit all changes
            session.commit()
            print(f"\n🎉 SUCCESS: All test data created successfully!")
            
            # Step 9: Display summary for testing
            print(f"\n📋 FUP TEST DATA SUMMARY:")
            print(f"   🏢 Location ID: {location_id}")
            print(f"   👤 Customer ID: {customer_id} (fup.test@example.com)")
            print(f"   🔧 Service ID: {service_id}")
            print(f"   🌐 Internet Service ID: {internet_service_id}")
            print(f"   📈 Current Usage: 450 GB / 500 GB limit")
            print(f"   ⚠️  FUP Threshold: 400 GB (EXCEEDED)")
            print(f"   🐌 FUP Speed: 10 Mbps (ACTIVE)")
            
            print(f"\n🧪 READY FOR FUP RESET TESTING:")
            print(f"   Endpoint: POST /api/v1/services/internet/{internet_service_id}/reset-fup")
            print(f"   Expected: Reset usage to 0, deactivate FUP, restore full speed")
            
            return {
                "customer_id": customer_id,
                "service_id": service_id,
                "internet_service_id": internet_service_id,
                "location_id": location_id,
                "customer_email": "fup.test@example.com"
            }
            
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return None

if __name__ == "__main__":
    result = create_comprehensive_fup_test_data()
    if result:
        print(f"\n✅ Test data creation completed successfully!")
        print(f"🚀 Ready to proceed with FUP reset validation!")
    else:
        print(f"\n❌ Test data creation failed!")
        sys.exit(1)
