#!/usr/bin/env python3
"""
Script to create a reseller account for admin access
"""
import sys
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append('/app')

from app.core.config import settings

def create_admin_reseller():
    """Create a reseller account for admin access"""
    try:
        # Create password context
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Hash the password
        password = "admin123"
        hashed_password = pwd_context.hash(password)
        
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # Check if admin reseller already exists
            result = session.execute(
                text("SELECT email FROM resellers WHERE email = :email"),
                {"email": "admin@ispframework.com"}
            )
            existing = result.fetchone()
            
            if existing:
                print("Admin reseller account already exists, updating password...")
                # Update existing reseller password
                result = session.execute(
                    text("UPDATE resellers SET password_hash = :password WHERE email = :email"),
                    {"password": hashed_password, "email": "admin@ispframework.com"}
                )
                session.commit()
                print(f"✅ Updated password for existing admin reseller")
            else:
                print("Creating new admin reseller account...")
                # Create new reseller account
                result = session.execute(
                    text("""
                    INSERT INTO resellers (
                        name, code, contact_person, email, phone, address, city, 
                        state_province, postal_code, country, commission_percentage, 
                        password_hash, is_active
                    ) VALUES (
                        :name, :code, :contact_person, :email, :phone, :address, :city,
                        :state_province, :postal_code, :country, :commission_percentage,
                        :password_hash, :is_active
                    )
                    """),
                    {
                        "name": "ISP Framework Admin",
                        "code": "ADMIN001",
                        "contact_person": "System Administrator",
                        "email": "admin@ispframework.com",
                        "phone": "+1-555-0000",
                        "address": "123 Admin St",
                        "city": "Admin City",
                        "state_province": "Admin State",
                        "postal_code": "00000",
                        "country": "US",
                        "commission_percentage": 0.0,
                        "password_hash": hashed_password,
                        "is_active": True
                    }
                )
                session.commit()
                print(f"✅ Created new admin reseller account")
            
            print(f"Email: admin@ispframework.com")
            print(f"Password: {password}")
                
    except Exception as e:
        print(f"❌ Error creating admin reseller: {e}")

if __name__ == "__main__":
    create_admin_reseller()
