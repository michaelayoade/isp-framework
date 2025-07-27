#!/usr/bin/env python3
"""
Migration Consolidation Script for ISP Framework

This script resolves migration dependency conflicts and establishes a clean linear migration path.
It addresses the following issues:
- Multiple conflicting head revisions
- Broken dependency chains
- Inconsistent revision ID formats
- Missing down_revision references

Usage:
    python scripts/consolidate_migrations.py [--dry-run] [--backup]
"""

import os
import sys
import re
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

class MigrationConsolidator:
    """Handles migration consolidation and dependency resolution"""
    
    def __init__(self, migrations_dir: Path, dry_run: bool = False, backup: bool = True):
        self.migrations_dir = migrations_dir
        self.dry_run = dry_run
        self.backup = backup
        self.migration_files = []
        self.migration_graph = {}
        self.consolidated_order = []
        
    def analyze_migrations(self) -> Dict[str, Dict]:
        """Analyze all migration files and extract metadata"""
        print("🔍 Analyzing migration files...")
        
        migrations = {}
        
        for file_path in self.migrations_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Extract revision metadata
                revision_match = re.search(r"revision:\s*str\s*=\s*['\"]([^'\"]+)['\"]", content)
                down_revision_match = re.search(r"down_revision:\s*Union\[str,\s*None\]\s*=\s*(?:['\"]([^'\"]*)['\"]|None)", content)
                
                if not revision_match:
                    # Try alternative format
                    revision_match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
                    down_revision_match = re.search(r"down_revision\s*=\s*(?:['\"]([^'\"]*)['\"]|None)", content)
                
                if revision_match:
                    revision_id = revision_match.group(1)
                    down_revision = down_revision_match.group(1) if down_revision_match and down_revision_match.group(1) else None
                    
                    # Extract description from docstring
                    desc_match = re.search(r'"""([^"]+)', content)
                    description = desc_match.group(1).strip() if desc_match else file_path.stem
                    
                    migrations[revision_id] = {
                        'file_path': file_path,
                        'revision_id': revision_id,
                        'down_revision': down_revision,
                        'description': description,
                        'content': content,
                        'file_name': file_path.name
                    }
                    
                    print(f"  📄 {file_path.name}: {revision_id} -> {down_revision}")
                    
            except Exception as e:
                print(f"  ❌ Error analyzing {file_path.name}: {e}")
                
        return migrations
    
    def build_dependency_graph(self, migrations: Dict[str, Dict]) -> Dict[str, List[str]]:
        """Build dependency graph from migration metadata"""
        print("\n🔗 Building dependency graph...")
        
        graph = {}
        for revision_id, migration in migrations.items():
            graph[revision_id] = []
            
            # Find migrations that depend on this one
            for other_id, other_migration in migrations.items():
                if other_migration['down_revision'] == revision_id:
                    graph[revision_id].append(other_id)
        
        return graph
    
    def find_root_migrations(self, migrations: Dict[str, Dict]) -> List[str]:
        """Find migrations with no dependencies (root migrations)"""
        roots = []
        for revision_id, migration in migrations.items():
            if not migration['down_revision']:
                roots.append(revision_id)
        return roots
    
    def topological_sort(self, migrations: Dict[str, Dict]) -> List[str]:
        """Perform topological sort to establish proper migration order"""
        print("\n📊 Establishing migration order...")
        
        # Find root migrations
        roots = self.find_root_migrations(migrations)
        print(f"  🌱 Root migrations: {roots}")
        
        # Build reverse dependency map
        dependents = {}
        for revision_id, migration in migrations.items():
            dependents[revision_id] = []
            
        for revision_id, migration in migrations.items():
            if migration['down_revision'] and migration['down_revision'] in dependents:
                dependents[migration['down_revision']].append(revision_id)
        
        # Perform topological sort
        visited = set()
        order = []
        
        def visit(revision_id):
            if revision_id in visited:
                return
            visited.add(revision_id)
            
            # Visit dependencies first
            if revision_id in dependents:
                for dependent in dependents[revision_id]:
                    visit(dependent)
            
            order.append(revision_id)
        
        # Start from roots
        for root in roots:
            visit(root)
        
        # Add any remaining migrations (in case of cycles)
        for revision_id in migrations:
            if revision_id not in visited:
                visit(revision_id)
        
        order.reverse()  # We want dependencies first
        return order
    
    def create_consolidated_order(self, migrations: Dict[str, Dict]) -> List[Tuple[str, str]]:
        """Create the proper consolidated migration order"""
        print("\n🎯 Creating consolidated migration order...")
        
        # Define the logical order based on ISP Framework architecture
        logical_order = [
            # Foundation
            ('7fbe30f0c3ed', 'Foundation: Basic customer model changes'),
            ('005_add_portal_id_uniqueness', 'Foundation: Portal ID system'),
            ('005a_add_locations_table', 'Foundation: Locations table'),
            
            # Core Infrastructure  
            ('006_add_network_infrastructure', 'Infrastructure: Network and IPAM'),
            ('007_add_radius_tables', 'Infrastructure: RADIUS sessions'),
            ('008_add_radius_clients', 'Infrastructure: RADIUS clients'),
            ('00ba038d8a2e', 'Infrastructure: Base tables'),
            
            # Business Logic
            ('4db3f05bfae9', 'Business: Service management'),
            ('35b46255a705', 'Business: Billing system'),
            ('9e1c7b520e78', 'Business: Comprehensive customer schema'),
            
            # Advanced Features
            ('create_ticketing_system', 'Features: Support ticketing system'),
            ('add_webhook_system', 'Features: Webhook integrations'),
            ('create_api_management_system', 'Features: API management'),
            ('2025_07_23_add_api_management', 'Features: Enhanced API management'),
            ('create_communications_system', 'Features: Communications system'),
            ('0016_create_file_storage_tables', 'Features: File storage system'),
            ('create_file_storage_system', 'Features: Enhanced file storage'),
            ('create_plugin_system_tables', 'Features: Plugin system'),
        ]
        
        # Filter to only include existing migrations
        consolidated = []
        for revision_id, description in logical_order:
            if revision_id in migrations:
                consolidated.append((revision_id, description))
                print(f"  ✅ {revision_id}: {description}")
            else:
                print(f"  ⚠️  {revision_id}: Not found, skipping")
        
        return consolidated
    
    def backup_migrations(self):
        """Create backup of current migration files"""
        if not self.backup:
            return
            
        backup_dir = self.migrations_dir.parent / f"migrations_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(exist_ok=True)
        
        print(f"\n💾 Creating backup at: {backup_dir}")
        
        for file_path in self.migrations_dir.glob("*.py"):
            if not file_path.name.startswith("__"):
                shutil.copy2(file_path, backup_dir / file_path.name)
                
        print(f"  ✅ Backed up {len(list(backup_dir.glob('*.py')))} migration files")
    
    def fix_migration_dependencies(self, migrations: Dict[str, Dict], order: List[Tuple[str, str]]):
        """Fix migration dependencies to create linear chain"""
        print("\n🔧 Fixing migration dependencies...")
        
        if self.dry_run:
            print("  🔍 DRY RUN - No files will be modified")
        
        previous_revision = None
        
        for i, (revision_id, description) in enumerate(order):
            if revision_id not in migrations:
                continue
                
            migration = migrations[revision_id]
            file_path = migration['file_path']
            content = migration['content']
            
            # Determine correct down_revision
            correct_down_revision = previous_revision
            current_down_revision = migration['down_revision']
            
            if current_down_revision != correct_down_revision:
                print(f"  🔄 {revision_id}: {current_down_revision} -> {correct_down_revision}")
                
                if not self.dry_run:
                    # Update down_revision in file content
                    if correct_down_revision:
                        # Replace down_revision value
                        content = re.sub(
                            r"down_revision:\s*Union\[str,\s*None\]\s*=\s*(?:['\"][^'\"]*['\"]|None)",
                            f"down_revision: Union[str, None] = '{correct_down_revision}'",
                            content
                        )
                        content = re.sub(
                            r"down_revision\s*=\s*(?:['\"][^'\"]*['\"]|None)",
                            f"down_revision = '{correct_down_revision}'",
                            content
                        )
                    else:
                        # Set to None for first migration
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
                    
                    # Write updated content
                    with open(file_path, 'w') as f:
                        f.write(content)
            else:
                print(f"  ✅ {revision_id}: Dependencies already correct")
            
            previous_revision = revision_id
    
    def generate_migration_summary(self, order: List[Tuple[str, str]]):
        """Generate a summary of the consolidated migration order"""
        summary_path = self.migrations_dir / "MIGRATION_ORDER.md"
        
        print(f"\n📋 Generating migration summary: {summary_path}")
        
        if self.dry_run:
            print("  🔍 DRY RUN - Summary file will not be created")
            return
        
        content = f"""# ISP Framework Migration Order

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This document outlines the consolidated migration order for the ISP Framework database schema.

## Migration Sequence

"""
        
        for i, (revision_id, description) in enumerate(order, 1):
            content += f"{i:2d}. **{revision_id}** - {description}\n"
        
        content += f"""

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
"""
        
        with open(summary_path, 'w') as f:
            f.write(content)
    
    def run_consolidation(self):
        """Run the complete migration consolidation process"""
        print("🚀 Starting Migration Consolidation for ISP Framework")
        print("=" * 60)
        
        # Step 1: Backup existing migrations
        self.backup_migrations()
        
        # Step 2: Analyze current migrations
        migrations = self.analyze_migrations()
        print(f"\n📊 Found {len(migrations)} migration files")
        
        # Step 3: Create consolidated order
        order = self.create_consolidated_order(migrations)
        print(f"\n🎯 Consolidated order contains {len(order)} migrations")
        
        # Step 4: Fix dependencies
        self.fix_migration_dependencies(migrations, order)
        
        # Step 5: Generate summary
        self.generate_migration_summary(order)
        
        print("\n" + "=" * 60)
        print("✅ Migration consolidation completed successfully!")
        
        if self.dry_run:
            print("🔍 This was a DRY RUN - no files were modified")
            print("   Run without --dry-run to apply changes")
        else:
            print("🎉 Migration dependencies have been fixed")
            print("   Run 'alembic upgrade head' to apply all migrations")


def main():
    parser = argparse.ArgumentParser(description='Consolidate ISP Framework database migrations')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup of migration files')
    
    args = parser.parse_args()
    
    # Find migrations directory
    backend_dir = Path(__file__).parent.parent
    migrations_dir = backend_dir / "alembic" / "versions"
    
    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    # Run consolidation
    consolidator = MigrationConsolidator(
        migrations_dir=migrations_dir,
        dry_run=args.dry_run,
        backup=not args.no_backup
    )
    
    try:
        consolidator.run_consolidation()
    except Exception as e:
        print(f"\n❌ Error during consolidation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
