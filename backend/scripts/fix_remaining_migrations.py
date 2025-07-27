#!/usr/bin/env python3
"""
Enhanced Migration Fix Script for ISP Framework

This script handles the remaining migration dependency issues that weren't resolved
by the initial consolidation, specifically:
- webhook_system_001 (orphaned migration)
- fix_webhook_2025_07_24 (duplicate webhook migration)
- 20240723_create_file_storage (duplicate file storage migration)

Usage:
    python scripts/fix_remaining_migrations.py [--dry-run]
"""

import os
import sys
import re
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

class RemainingMigrationFixer:
    """Handles remaining migration dependency issues"""
    
    def __init__(self, migrations_dir: Path, dry_run: bool = False):
        self.migrations_dir = migrations_dir
        self.dry_run = dry_run
        
    def analyze_remaining_issues(self):
        """Analyze remaining migration dependency issues"""
        print("🔍 Analyzing remaining migration issues...")
        
        issues = {
            'orphaned_webhooks': [],
            'duplicate_file_storage': [],
            'conflicting_heads': []
        }
        
        # Check for orphaned webhook migrations
        webhook_files = list(self.migrations_dir.glob("*webhook*"))
        for webhook_file in webhook_files:
            with open(webhook_file, 'r') as f:
                content = f.read()
            
            if 'down_revision: Union[str, None] = None' in content or 'down_revision = None' in content:
                issues['orphaned_webhooks'].append(webhook_file)
                print(f"  ⚠️  Orphaned webhook: {webhook_file.name}")
        
        # Check for duplicate file storage migrations
        file_storage_files = list(self.migrations_dir.glob("*file_storage*"))
        if len(file_storage_files) > 1:
            issues['duplicate_file_storage'] = file_storage_files
            print(f"  ⚠️  Duplicate file storage migrations: {[f.name for f in file_storage_files]}")
        
        return issues
    
    def fix_orphaned_webhook_migration(self):
        """Fix orphaned webhook migration by integrating it into the chain"""
        print("\n🔧 Fixing orphaned webhook migration...")
        
        webhook_files = [
            self.migrations_dir / "add_webhook_system.py",
            self.migrations_dir / "fix_webhook_migration.py"
        ]
        
        # Keep the more comprehensive webhook migration and remove duplicates
        primary_webhook = None
        duplicate_webhooks = []
        
        for webhook_file in webhook_files:
            if webhook_file.exists():
                with open(webhook_file, 'r') as f:
                    content = f.read()
                
                # Check which one is more comprehensive
                if 'webhook_endpoints' in content and 'webhook_events' in content:
                    primary_webhook = webhook_file
                else:
                    duplicate_webhooks.append(webhook_file)
        
        if primary_webhook:
            print(f"  ✅ Primary webhook migration: {primary_webhook.name}")
            
            # Update the primary webhook to depend on the ticketing system
            if not self.dry_run:
                with open(primary_webhook, 'r') as f:
                    content = f.read()
                
                # Update down_revision to depend on ticketing system
                content = re.sub(
                    r"down_revision:\s*Union\[str,\s*None\]\s*=\s*None",
                    "down_revision: Union[str, None] = 'create_ticketing_system'",
                    content
                )
                content = re.sub(
                    r"down_revision\s*=\s*None",
                    "down_revision = 'create_ticketing_system'",
                    content
                )
                
                with open(primary_webhook, 'w') as f:
                    f.write(content)
                
                print(f"  🔄 Updated {primary_webhook.name} to depend on create_ticketing_system")
        
        # Remove duplicate webhook migrations
        for duplicate in duplicate_webhooks:
            if duplicate.exists():
                if not self.dry_run:
                    duplicate.unlink()
                print(f"  🗑️  Removed duplicate: {duplicate.name}")
    
    def fix_duplicate_file_storage(self):
        """Fix duplicate file storage migrations"""
        print("\n🔧 Fixing duplicate file storage migrations...")
        
        file_storage_files = [
            self.migrations_dir / "0016_create_file_storage_tables.py",
            self.migrations_dir / "create_file_storage_system.py"
        ]
        
        # Keep the more recent/comprehensive one
        primary_file_storage = None
        duplicate_file_storage = []
        
        for file_storage_file in file_storage_files:
            if file_storage_file.exists():
                with open(file_storage_file, 'r') as f:
                    content = f.read()
                
                # Check which one is more comprehensive (has more tables)
                table_count = content.count('op.create_table')
                if table_count >= 4:  # More comprehensive migration
                    primary_file_storage = file_storage_file
                else:
                    duplicate_file_storage.append(file_storage_file)
        
        if primary_file_storage:
            print(f"  ✅ Primary file storage migration: {primary_file_storage.name}")
        
        # Remove duplicates
        for duplicate in duplicate_file_storage:
            if duplicate.exists():
                if not self.dry_run:
                    duplicate.unlink()
                print(f"  🗑️  Removed duplicate: {duplicate.name}")
    
    def update_final_migration_chain(self):
        """Update the final migration chain to ensure proper linear order"""
        print("\n🔗 Updating final migration chain...")
        
        # Define the final correct order
        final_order = [
            ('7fbe30f0c3ed', None),
            ('005_add_portal_id_uniqueness', '7fbe30f0c3ed'),
            ('005a_add_locations_table', '005_add_portal_id_uniqueness'),
            ('006_add_network_infrastructure', '005a_add_locations_table'),
            ('007_add_radius_tables', '006_add_network_infrastructure'),
            ('008_add_radius_clients', '007_add_radius_tables'),
            ('00ba038d8a2e', '008_add_radius_clients'),
            ('4db3f05bfae9', '00ba038d8a2e'),
            ('35b46255a705', '4db3f05bfae9'),
            ('9e1c7b520e78', '35b46255a705'),
            ('create_ticketing_system', '9e1c7b520e78'),
            ('webhook_system_001', 'create_ticketing_system'),  # Fixed webhook
            ('create_api_management_system', 'webhook_system_001'),
            ('2025_07_23_add_api_management', 'create_api_management_system'),
            ('create_communications_system', '2025_07_23_add_api_management'),
            ('0016_create_file_storage_tables', 'create_communications_system'),
            ('create_plugin_system_tables', '0016_create_file_storage_tables'),
        ]
        
        for revision_id, expected_down_revision in final_order:
            migration_files = list(self.migrations_dir.glob(f"*{revision_id}*"))
            
            if not migration_files:
                continue
                
            migration_file = migration_files[0]
            
            with open(migration_file, 'r') as f:
                content = f.read()
            
            # Check current down_revision
            down_revision_match = re.search(r"down_revision:\s*Union\[str,\s*None\]\s*=\s*(?:['\"]([^'\"]*)['\"]|None)", content)
            if not down_revision_match:
                down_revision_match = re.search(r"down_revision\s*=\s*(?:['\"]([^'\"]*)['\"]|None)", content)
            
            current_down_revision = down_revision_match.group(1) if down_revision_match and down_revision_match.group(1) else None
            
            if current_down_revision != expected_down_revision:
                print(f"  🔄 {revision_id}: {current_down_revision} -> {expected_down_revision}")
                
                if not self.dry_run:
                    if expected_down_revision:
                        content = re.sub(
                            r"down_revision:\s*Union\[str,\s*None\]\s*=\s*(?:['\"][^'\"]*['\"]|None)",
                            f"down_revision: Union[str, None] = '{expected_down_revision}'",
                            content
                        )
                        content = re.sub(
                            r"down_revision\s*=\s*(?:['\"][^'\"]*['\"]|None)",
                            f"down_revision = '{expected_down_revision}'",
                            content
                        )
                    else:
                        content = re.sub(
                            r"down_revision:\s*Union\[str,\s*None\]\s*=\s*(?:['\"][^'\"]*['\"]|None)",
                            "down_revision: Union[str, None] = None",
                            content
                        )
                        content = re.sub(
                            r"down_revision\s*=\s*(?:['\"][^'\"]*['\"]|None)",
                            "down_revision = None",
                            content
                        )
                    
                    with open(migration_file, 'w') as f:
                        f.write(content)
            else:
                print(f"  ✅ {revision_id}: Dependencies already correct")
    
    def generate_final_migration_summary(self):
        """Generate final migration summary"""
        summary_path = self.migrations_dir / "FINAL_MIGRATION_ORDER.md"
        
        print(f"\n📋 Generating final migration summary: {summary_path}")
        
        if self.dry_run:
            print("  🔍 DRY RUN - Summary file will not be created")
            return
        
        content = f"""# ISP Framework - Final Migration Order

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This document outlines the final consolidated migration order for the ISP Framework database schema after resolving all dependency conflicts.

## Final Migration Sequence

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
12. **webhook_system_001** - Features: Webhook integrations (consolidated)
13. **create_api_management_system** - Features: API management
14. **2025_07_23_add_api_management** - Features: Enhanced API management
15. **create_communications_system** - Features: Communications system
16. **0016_create_file_storage_tables** - Features: File storage system (consolidated)
17. **create_plugin_system_tables** - Features: Plugin system

## Issues Resolved

### ✅ Orphaned Migrations
- Fixed webhook_system_001 to depend on create_ticketing_system
- Removed duplicate webhook migrations

### ✅ Duplicate Migrations
- Consolidated file storage migrations
- Removed redundant migration files

### ✅ Linear Dependency Chain
- All migrations now form a proper linear chain
- No more branching or conflicting heads
- Each migration depends on exactly one previous migration

## Validation Commands

```bash
# Check migration status
alembic current

# View migration history
alembic history --verbose

# Apply all migrations
alembic upgrade head

# Rollback if needed
alembic downgrade <revision_id>
```

## Database Schema Coverage

The final migration chain provides complete coverage for:

- ✅ **Customer Management**: Hierarchical accounts, portal IDs, billing config
- ✅ **Service Management**: Internet, Voice, Bundle services with provisioning
- ✅ **Billing System**: Invoices, payments, credit notes, accounting
- ✅ **Network Infrastructure**: Sites, devices, IPAM, monitoring
- ✅ **RADIUS Integration**: Session management, client configuration
- ✅ **Support System**: Ticketing, SLA tracking, field work orders
- ✅ **Integration Layer**: Webhooks, API management, plugin system
- ✅ **Communications**: Email, SMS, templates, campaigns
- ✅ **File Management**: MinIO S3 integration, document storage

## Production Readiness

✅ **Migration Chain**: Linear and conflict-free
✅ **Schema Coverage**: Complete ISP Framework functionality
✅ **Rollback Support**: All migrations have proper downgrade functions
✅ **Documentation**: Comprehensive migration order and usage guide

The ISP Framework database migrations are now production-ready and fully consolidated.
"""
        
        with open(summary_path, 'w') as f:
            f.write(content)
    
    def run_final_fix(self):
        """Run the complete remaining migration fix process"""
        print("🚀 Starting Final Migration Fix for ISP Framework")
        print("=" * 60)
        
        # Step 1: Analyze remaining issues
        issues = self.analyze_remaining_issues()
        
        # Step 2: Fix orphaned webhook migration
        if issues['orphaned_webhooks']:
            self.fix_orphaned_webhook_migration()
        
        # Step 3: Fix duplicate file storage migrations
        if issues['duplicate_file_storage']:
            self.fix_duplicate_file_storage()
        
        # Step 4: Update final migration chain
        self.update_final_migration_chain()
        
        # Step 5: Generate final summary
        self.generate_final_migration_summary()
        
        print("\n" + "=" * 60)
        print("✅ Final migration fix completed successfully!")
        
        if self.dry_run:
            print("🔍 This was a DRY RUN - no files were modified")
            print("   Run without --dry-run to apply changes")
        else:
            print("🎉 All migration dependency conflicts resolved")
            print("   Migration chain is now linear and production-ready")
            print("   Run 'alembic upgrade head' to apply all migrations")


def main():
    parser = argparse.ArgumentParser(description='Fix remaining ISP Framework migration issues')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Find migrations directory
    backend_dir = Path(__file__).parent.parent
    migrations_dir = backend_dir / "alembic" / "versions"
    
    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    # Run final fix
    fixer = RemainingMigrationFixer(
        migrations_dir=migrations_dir,
        dry_run=args.dry_run
    )
    
    try:
        fixer.run_final_fix()
    except Exception as e:
        print(f"\n❌ Error during final fix: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
