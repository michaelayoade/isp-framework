#!/usr/bin/env python3
"""
Script to check admin credentials in the database
"""
import asyncio
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append('/app')

from app.core.config import settings

def check_admin_credentials():
    """Check what admin credentials exist in the database"""
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # Check administrators table structure first
            result = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'administrators';"))
            admin_columns = [row[0] for row in result.fetchall()]
            print(f"=== Administrator Table Columns ===")
            print(f"Available columns: {admin_columns}")
            
            # Query administrators table with available columns
            if 'email' in admin_columns:
                available_cols = [col for col in ['email', 'full_name', 'is_active', 'password_hash', 'hashed_password'] if col in admin_columns]
                col_str = ', '.join(available_cols)
                result = session.execute(text(f"SELECT {col_str} FROM administrators LIMIT 10;"))
                admins = result.fetchall()
                
                print("\n=== Administrator Accounts ===")
                if not admins:
                    print("No administrator accounts found.")
                else:
                    for i, admin in enumerate(admins):
                        print(f"Admin {i+1}: {admin}")
            
            # Check resellers table structure first
            result = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'resellers';"))
            reseller_columns = [row[0] for row in result.fetchall()]
            print(f"\n=== Reseller Table Columns ===")
            print(f"Available columns: {reseller_columns}")
            
            # Query resellers with available columns
            if 'email' in reseller_columns:
                available_cols = [col for col in ['email', 'name', 'company_name', 'is_active'] if col in reseller_columns]
                col_str = ', '.join(available_cols)
                result = session.execute(text(f"SELECT {col_str} FROM resellers LIMIT 10;"))
                resellers = result.fetchall()
                
                print("\n=== Reseller Accounts ===")
                if not resellers:
                    print("No reseller accounts found.")
                else:
                    for reseller in resellers:
                        print(f"Reseller: {reseller}")
                    
    except Exception as e:
        print(f"Error checking credentials: {e}")

if __name__ == "__main__":
    check_admin_credentials()
