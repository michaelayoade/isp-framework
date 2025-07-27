# ISP Framework Migration Order

Generated on: 2025-07-26 01:15:42

This document outlines the consolidated migration order for the ISP Framework database schema.

## Migration Sequence

 1. **7fbe30f0c3ed** - Foundation: Basic customer model changes
 2. **005_add_portal_id_uniqueness** - Foundation: Portal ID system
 3. **005a_add_locations_table** - Foundation: Locations table
 4. **006_add_network_infrastructure** - Infrastructure: Network and IPAM
 5. **007_add_radius_tables** - Infrastructure: RADIUS sessions
 6. **008_add_radius_clients** - Infrastructure: RADIUS clients
 7. **00ba038d8a2e** - Infrastructure: Base tables
 8. **4db3f05bfae9** - Business: Service management
 9. **35b46255a705** - Business: Billing system
10. **9e1c7b520e78** - Business: Comprehensive customer schema
11. **create_ticketing_system** - Features: Support ticketing system
12. **create_api_management_system** - Features: API management
13. **2025_07_23_add_api_management** - Features: Enhanced API management
14. **create_communications_system** - Features: Communications system
15. **0016_create_file_storage_tables** - Features: File storage system
16. **create_plugin_system_tables** - Features: Plugin system


## Migration Categories

### Foundation (1-3)
- Basic customer model and portal ID system
- Location infrastructure

### Infrastructure (4-7) 
- Network infrastructure and IPAM
- RADIUS integration
- Base system tables

### Business Logic (8-10)
- Service management
- Billing system  
- Customer schema enhancements

### Advanced Features (11+)
- Support ticketing
- Webhook integrations
- API management
- Communications
- File storage
- Plugin system

## Usage

To apply all migrations in order:
```bash
cd backend
alembic upgrade head
```

To check current migration status:
```bash
alembic current
alembic history --verbose
```

## Notes

- All migrations have been consolidated into a linear dependency chain
- Each migration depends on the previous one in the sequence
- Rollback support is maintained through proper downgrade() functions
- Backup of original migrations available in migrations_backup_* directory
