#!/usr/bin/env python3
"""
Script to reset admin password to a known value for testing
"""
import sys
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append('/app')

from app.core.config import settings

def reset_admin_password():
    """Reset admin password to 'admin123' for testing"""
    try:
        # Create password context (same as used in the app)
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Hash the new password
        new_password = "admin123"
        hashed_password = pwd_context.hash(new_password)
        
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # Update the admin password
            result = session.execute(
                text("UPDATE administrators SET hashed_password = :password WHERE email = :email"),
                {"password": hashed_password, "email": "admin@ispframework.com"}
            )
            session.commit()
            
            if result.rowcount > 0:
                print(f"✅ Successfully reset password for admin@ispframework.com")
                print(f"New password: {new_password}")
                print(f"Password hash: {hashed_password[:50]}...")
            else:
                print("❌ No admin account found to update")
                
    except Exception as e:
        print(f"❌ Error resetting password: {e}")

if __name__ == "__main__":
    reset_admin_password()
