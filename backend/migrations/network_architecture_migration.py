#!/usr/bin/env python3
"""
Network Architecture Migration Script

This script migrates data from legacy network models (network.py) to the new
modular architecture (networks.py, ipam.py, nas_radius.py, vendor modules).

Migration Strategy:
1. Preserve existing data while transitioning to new models
2. Extract vendor-specific logic to dedicated modules
3. Remove multi-tenant logic (partners_ids) for single-tenant architecture
4. Maintain referential integrity throughout migration

Usage:
    python network_architecture_migration.py --phase [1|2|3|4|5]
    python network_architecture_migration.py --rollback --phase [1|2|3|4|5]
"""

import sys
import argparse
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NetworkMigrationManager:
    """Manages the migration from legacy to modular network architecture"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.migration_log = []
    
    def log_migration_step(self, phase: int, step: str, status: str, details: str = ""):
        """Log migration steps for audit trail"""
        entry = {
            "timestamp": datetime.now(timezone.utc),
            "phase": phase,
            "step": step,
            "status": status,
            "details": details
        }
        self.migration_log.append(entry)
        logger.info(f"Phase {phase} - {step}: {status} - {details}")
    
    def create_migration_tables(self, db: Session):
        """Create migration tracking tables"""
        try:
            # Create migration log table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS network_migration_log (
                    id SERIAL PRIMARY KEY,
                    phase INTEGER NOT NULL,
                    step VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            
            # Create backup tables for rollback
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS legacy_network_backup (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(255) NOT NULL,
                    record_id INTEGER NOT NULL,
                    backup_data JSONB NOT NULL,
                    backup_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            
            db.commit()
            self.log_migration_step(0, "create_migration_tables", "SUCCESS", 
                                  "Migration tracking tables created")
            
        except SQLAlchemyError as e:
            db.rollback()
            self.log_migration_step(0, "create_migration_tables", "ERROR", str(e))
            raise
    
    def backup_legacy_data(self, db: Session, table_name: str):
        """Create backup of legacy data before migration"""
        try:
            # Get all records from legacy table
            result = db.execute(text(f"SELECT * FROM {table_name}"))
            records = result.fetchall()
            
            # Store backup data
            for record in records:
                record_dict = dict(record._mapping)
                db.execute(text("""
                    INSERT INTO legacy_network_backup (table_name, record_id, backup_data)
                    VALUES (:table_name, :record_id, :backup_data)
                """), {
                    "table_name": table_name,
                    "record_id": record_dict.get('id', 0),
                    "backup_data": record_dict
                })
            
            db.commit()
            self.log_migration_step(1, f"backup_{table_name}", "SUCCESS", 
                                  f"Backed up {len(records)} records")
            return len(records)
            
        except SQLAlchemyError as e:
            db.rollback()
            self.log_migration_step(1, f"backup_{table_name}", "ERROR", str(e))
            raise
    
    def phase_1_data_preservation(self, db: Session):
        """Phase 1: Backup existing data and create new tables"""
        logger.info("Starting Phase 1: Data Preservation")
        
        # List of legacy tables to backup
        legacy_tables = [
            "network_sites",
            "ipv4_networks", 
            "ipv4_ips",
            "ipv6_networks",
            "ipv6_ips", 
            "routers",
            "router_sectors",
            "monitoring_devices",
            "monitoring_device_types",
            "monitoring_groups",
            "monitoring_producers"
        ]
        
        total_records = 0
        for table in legacy_tables:
            try:
                # Check if table exists
                result = db.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = :table_name
                    )
                """), {"table_name": table})
                
                if result.scalar():
                    count = self.backup_legacy_data(db, table)
                    total_records += count
                else:
                    self.log_migration_step(1, f"backup_{table}", "SKIPPED", 
                                          "Table does not exist")
                    
            except Exception as e:
                self.log_migration_step(1, f"backup_{table}", "ERROR", str(e))
                continue
        
        self.log_migration_step(1, "phase_1_complete", "SUCCESS", 
                              f"Backed up {total_records} total records")
        return total_records
    
    def phase_2_create_modular_tables(self, db: Session):
        """Phase 2: Create new modular architecture tables"""
        logger.info("Starting Phase 2: Create Modular Tables")
        
        # Create new modular network tables
        modular_tables = {
            "network_sites_new": """
                CREATE TABLE IF NOT EXISTS network_sites_new (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    site_code VARCHAR(50) UNIQUE,
                    site_type VARCHAR(50) NOT NULL,
                    address TEXT,
                    latitude VARCHAR(20),
                    longitude VARCHAR(20),
                    elevation INTEGER,
                    description TEXT,
                    contact_person VARCHAR(255),
                    contact_phone VARCHAR(50),
                    contact_email VARCHAR(255),
                    power_backup BOOLEAN DEFAULT FALSE,
                    cooling_system BOOLEAN DEFAULT FALSE,
                    security_system BOOLEAN DEFAULT FALSE,
                    rack_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    maintenance_window VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """,
            
            "network_devices": """
                CREATE TABLE IF NOT EXISTS network_devices (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    device_type VARCHAR(50) NOT NULL,
                    site_id INTEGER REFERENCES network_sites_new(id),
                    vendor VARCHAR(100),
                    model VARCHAR(255),
                    serial_number VARCHAR(255) UNIQUE,
                    firmware_version VARCHAR(100),
                    management_ip INET,
                    rack_position VARCHAR(50),
                    power_consumption INTEGER,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_monitored BOOLEAN DEFAULT TRUE,
                    last_seen TIMESTAMP WITH TIME ZONE,
                    uptime_seconds INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """,
            
            "ip_pools": """
                CREATE TABLE IF NOT EXISTS ip_pools (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    network INET NOT NULL,
                    prefix_length INTEGER NOT NULL,
                    pool_type VARCHAR(50) NOT NULL,
                    description TEXT,
                    location_id INTEGER REFERENCES locations(id),
                    vlan_id INTEGER,
                    gateway INET,
                    dns_servers INET[],
                    is_active BOOLEAN DEFAULT TRUE,
                    allow_auto_assignment BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """,
            
            "ip_allocations": """
                CREATE TABLE IF NOT EXISTS ip_allocations (
                    id SERIAL PRIMARY KEY,
                    pool_id INTEGER REFERENCES ip_pools(id),
                    ip_address INET NOT NULL,
                    allocation_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    customer_id INTEGER REFERENCES customers(id),
                    device_id INTEGER REFERENCES network_devices(id),
                    service_id INTEGER,
                    hostname VARCHAR(255),
                    description TEXT,
                    allocated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    last_seen TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    UNIQUE(ip_address)
                );
            """
        }
        
        created_tables = 0
        for table_name, create_sql in modular_tables.items():
            try:
                db.execute(text(create_sql))
                db.commit()
                created_tables += 1
                self.log_migration_step(2, f"create_{table_name}", "SUCCESS", 
                                      "Table created successfully")
                
            except SQLAlchemyError as e:
                db.rollback()
                self.log_migration_step(2, f"create_{table_name}", "ERROR", str(e))
                continue
        
        self.log_migration_step(2, "phase_2_complete", "SUCCESS", 
                              f"Created {created_tables} modular tables")
        return created_tables
    
    def phase_3_migrate_network_sites(self, db: Session):
        """Phase 3: Migrate network sites to new architecture"""
        logger.info("Starting Phase 3: Migrate Network Sites")
        
        try:
            # Get legacy network sites
            result = db.execute(text("""
                SELECT id, title, description, address, gps, location_id
                FROM network_sites
                ORDER BY id
            """))
            legacy_sites = result.fetchall()
            
            migrated_count = 0
            for site in legacy_sites:
                # Parse GPS coordinates if available
                latitude, longitude = None, None
                if site.gps:
                    try:
                        coords = site.gps.split(',')
                        if len(coords) == 2:
                            latitude = coords[0].strip()
                            longitude = coords[1].strip()
                    except:
                        pass
                
                # Generate site code from name
                site_code = site.title.lower().replace(' ', '_').replace('-', '_')[:50]
                
                # Insert into new table
                db.execute(text("""
                    INSERT INTO network_sites_new 
                    (name, site_code, site_type, address, latitude, longitude, 
                     description, is_active, created_at)
                    VALUES (:name, :site_code, :site_type, :address, :latitude, 
                            :longitude, :description, :is_active, NOW())
                """), {
                    "name": site.title,
                    "site_code": f"{site_code}_{site.id}",  # Ensure uniqueness
                    "site_type": "pop",  # Default type
                    "address": site.address,
                    "latitude": latitude,
                    "longitude": longitude,
                    "description": site.description,
                    "is_active": True
                })
                
                migrated_count += 1
            
            db.commit()
            self.log_migration_step(3, "migrate_network_sites", "SUCCESS", 
                                  f"Migrated {migrated_count} network sites")
            return migrated_count
            
        except SQLAlchemyError as e:
            db.rollback()
            self.log_migration_step(3, "migrate_network_sites", "ERROR", str(e))
            raise
    
    def phase_4_migrate_ip_management(self, db: Session):
        """Phase 4: Migrate IP networks and addresses to IPAM"""
        logger.info("Starting Phase 4: Migrate IP Management")
        
        try:
            # Migrate IPv4 networks to IP pools
            result = db.execute(text("""
                SELECT id, network, mask, title, comment, location_id, 
                       network_type, type_of_usage
                FROM ipv4_networks
                ORDER BY id
            """))
            legacy_networks = result.fetchall()
            
            migrated_pools = 0
            for network in legacy_networks:
                # Determine pool type from legacy fields
                pool_type = "customer" if network.type_of_usage == "pool" else "infrastructure"
                
                db.execute(text("""
                    INSERT INTO ip_pools 
                    (name, network, prefix_length, pool_type, description, 
                     location_id, is_active, created_at)
                    VALUES (:name, :network, :prefix_length, :pool_type, 
                            :description, :location_id, :is_active, NOW())
                """), {
                    "name": network.title,
                    "network": network.network,
                    "prefix_length": network.mask,
                    "pool_type": pool_type,
                    "description": network.comment,
                    "location_id": network.location_id,
                    "is_active": True
                })
                
                migrated_pools += 1
            
            # Migrate IPv4 addresses to IP allocations
            result = db.execute(text("""
                SELECT ip.id, ip.ip, ip.hostname, ip.title, ip.comment, 
                       ip.is_used, ip.customer_id, ip.ipv4_networks_id,
                       net.title as network_title
                FROM ipv4_ips ip
                JOIN ipv4_networks net ON ip.ipv4_networks_id = net.id
                ORDER BY ip.id
            """))
            legacy_ips = result.fetchall()
            
            migrated_ips = 0
            for ip_record in legacy_ips:
                # Get corresponding pool ID
                pool_result = db.execute(text("""
                    SELECT id FROM ip_pools WHERE name = :network_title LIMIT 1
                """), {"network_title": ip_record.network_title})
                pool = pool_result.fetchone()
                
                if pool:
                    allocation_type = "static" if ip_record.customer_id else "reserved"
                    status = "allocated" if ip_record.is_used else "available"
                    
                    db.execute(text("""
                        INSERT INTO ip_allocations 
                        (pool_id, ip_address, allocation_type, status, 
                         customer_id, hostname, description, created_at)
                        VALUES (:pool_id, :ip_address, :allocation_type, 
                                :status, :customer_id, :hostname, :description, NOW())
                    """), {
                        "pool_id": pool.id,
                        "ip_address": ip_record.ip,
                        "allocation_type": allocation_type,
                        "status": status,
                        "customer_id": ip_record.customer_id,
                        "hostname": ip_record.hostname,
                        "description": ip_record.comment
                    })
                    
                    migrated_ips += 1
            
            db.commit()
            self.log_migration_step(4, "migrate_ip_management", "SUCCESS", 
                                  f"Migrated {migrated_pools} pools and {migrated_ips} IPs")
            return migrated_pools + migrated_ips
            
        except SQLAlchemyError as e:
            db.rollback()
            self.log_migration_step(4, "migrate_ip_management", "ERROR", str(e))
            raise
    
    def phase_5_extract_vendor_logic(self, db: Session):
        """Phase 5: Extract vendor-specific logic to dedicated modules"""
        logger.info("Starting Phase 5: Extract Vendor Logic")
        
        try:
            # Get routers with MikroTik-specific fields
            result = db.execute(text("""
                SELECT id, title, model, ip, api_login, api_password, api_port,
                       api_enable, nas_type, radius_secret, platform, version
                FROM routers
                WHERE api_login IS NOT NULL OR platform IS NOT NULL
                ORDER BY id
            """))
            legacy_routers = result.fetchall()
            
            # Create network devices (vendor-agnostic)
            migrated_devices = 0
            for router in legacy_routers:
                # Insert into network_devices
                device_result = db.execute(text("""
                    INSERT INTO network_devices 
                    (name, device_type, vendor, model, management_ip, 
                     firmware_version, is_active, created_at)
                    VALUES (:name, :device_type, :vendor, :model, :management_ip,
                            :firmware_version, :is_active, NOW())
                    RETURNING id
                """), {
                    "name": router.title,
                    "device_type": "router",
                    "vendor": "mikrotik" if router.platform else "unknown",
                    "model": router.model,
                    "management_ip": router.ip,
                    "firmware_version": router.version,
                    "is_active": True
                })
                
                device_id = device_result.scalar()
                
                # Insert MikroTik-specific data if applicable
                if router.api_login and router.platform:
                    db.execute(text("""
                        INSERT INTO mikrotik_devices 
                        (device_id, routeros_version, api_enabled, api_port,
                         api_username, api_password, created_at)
                        VALUES (:device_id, :routeros_version, :api_enabled,
                                :api_port, :api_username, :api_password, NOW())
                    """), {
                        "device_id": device_id,
                        "routeros_version": router.version or "unknown",
                        "api_enabled": router.api_enable or False,
                        "api_port": router.api_port or 8728,
                        "api_username": router.api_login,
                        "api_password": router.api_password
                    })
                
                migrated_devices += 1
            
            db.commit()
            self.log_migration_step(5, "extract_vendor_logic", "SUCCESS", 
                                  f"Extracted vendor logic for {migrated_devices} devices")
            return migrated_devices
            
        except SQLAlchemyError as e:
            db.rollback()
            self.log_migration_step(5, "extract_vendor_logic", "ERROR", str(e))
            raise
    
    def run_migration(self, phase: int = None):
        """Run the complete migration or specific phase"""
        with self.SessionLocal() as db:
            try:
                # Create migration infrastructure
                self.create_migration_tables(db)
                
                if phase is None or phase == 1:
                    self.phase_1_data_preservation(db)
                
                if phase is None or phase == 2:
                    self.phase_2_create_modular_tables(db)
                
                if phase is None or phase == 3:
                    self.phase_3_migrate_network_sites(db)
                
                if phase is None or phase == 4:
                    self.phase_4_migrate_ip_management(db)
                
                if phase is None or phase == 5:
                    self.phase_5_extract_vendor_logic(db)
                
                logger.info("Migration completed successfully!")
                return True
                
            except Exception as e:
                logger.error(f"Migration failed: {str(e)}")
                return False
    
    def rollback_migration(self, phase: int):
        """Rollback specific migration phase"""
        logger.info(f"Rolling back Phase {phase}")
        # Implementation for rollback logic
        # This would restore from backup tables
        pass


def main():
    parser = argparse.ArgumentParser(description='Network Architecture Migration')
    parser.add_argument('--phase', type=int, choices=[1,2,3,4,5], 
                       help='Run specific migration phase')
    parser.add_argument('--rollback', action='store_true', 
                       help='Rollback migration')
    parser.add_argument('--database-url', type=str, 
                       default='postgresql://ispframework:ispframework123@localhost:5432/ispframework',
                       help='Database connection URL')
    
    args = parser.parse_args()
    
    migration_manager = NetworkMigrationManager(args.database_url)
    
    if args.rollback:
        migration_manager.rollback_migration(args.phase)
    else:
        migration_manager.run_migration(args.phase)


if __name__ == "__main__":
    main()
