#!/usr/bin/env python3
"""
Pydantic v2 Migration Script
Automatically migrates deprecated @validator decorators to @field_validator
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


class PydanticMigrator:
    """Migrates Pydantic v1 validators to v2 field_validators."""
    
    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.files_modified = 0
        self.validators_migrated = 0
        
    def find_schema_files(self) -> List[Path]:
        """Find all Python files that likely contain Pydantic schemas."""
        schema_files = []
        
        # Look for schema files
        for pattern in ["**/schemas/*.py", "**/models/*.py"]:
            schema_files.extend(self.backend_path.glob(pattern))
        
        # Filter out __init__.py and other non-schema files
        return [f for f in schema_files if f.name != "__init__.py"]
    
    def migrate_file(self, file_path: Path) -> bool:
        """Migrate a single file from Pydantic v1 to v2 validators."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Check if file uses validators
            if '@validator(' not in content:
                return False
            
            print(f"🔄 Migrating {file_path.relative_to(self.backend_path)}")
            
            # 1. Update imports
            content = self._update_imports(content)
            
            # 2. Migrate @validator decorators
            content = self._migrate_validators(content)
            
            # 3. Update validator method signatures
            content = self._update_validator_signatures(content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.files_modified += 1
                return True
                
        except Exception as e:
            print(f"❌ Error migrating {file_path}: {e}")
            return False
        
        return False
    
    def _update_imports(self, content: str) -> str:
        """Update import statements to include field_validator."""
        # Pattern to match pydantic imports
        import_pattern = r'from pydantic import ([^\\n]+)'
        
        def replace_import(match):
            imports = match.group(1)
            
            # Add field_validator if not present and validator is present
            if 'validator' in imports and 'field_validator' not in imports:
                # Replace 'validator' with 'field_validator'
                imports = imports.replace('validator', 'field_validator')
            
            return f'from pydantic import {imports}'
        
        return re.sub(import_pattern, replace_import, content)
    
    def _migrate_validators(self, content: str) -> str:
        """Migrate @validator decorators to @field_validator."""
        # Pattern to match @validator decorators
        validator_pattern = r'@validator\('
        content = re.sub(validator_pattern, '@field_validator(', content)
        
        return content
    
    def _update_validator_signatures(self, content: str) -> str:
        """Update validator method signatures for Pydantic v2."""
        # Pattern to match validator method definitions
        # Matches: def method_name(cls, v, values):
        method_pattern = r'(\s+@field_validator\([^)]+\)\\s*\\n\s+)def (\w+)\(cls, v(?:, values)?\):'
        
        def replace_method(match):
            decorator_and_whitespace = match.group(1)
            method_name = match.group(2)
            
            # Add @classmethod decorator and update signature
            return f'{decorator_and_whitespace}@classmethod\\n    def {method_name}(cls, v, info=None):'
        
        content = re.sub(method_pattern, replace_method, content, flags=re.MULTILINE)
        
        # Also handle cases where @classmethod is already present
        # Pattern: @field_validator(...)\n    def method(cls, v, values):
        existing_classmethod_pattern = r'(@field_validator\([^)]+\)\\s*\\n\s+)def (\w+)\(cls, v, values\):'
        
        def replace_existing(match):
            decorator = match.group(1)
            method_name = match.group(2)
            return f'{decorator}@classmethod\\n    def {method_name}(cls, v, info=None):'
        
        content = re.sub(existing_classmethod_pattern, replace_existing, content, flags=re.MULTILINE)
        
        # Update references to 'values' parameter to use 'info.data'
        content = self._update_values_references(content)
        
        return content
    
    def _update_values_references(self, content: str) -> str:
        """Update references to 'values' parameter to use 'info.data'."""
        # Replace values['field'] with info.data['field'] (with safety check)
        values_pattern = r"values\['([^']+)'\]"
        content = re.sub(values_pattern, r"(info.data.get('\1') if info and hasattr(info, 'data') else None)", content)
        
        # Replace 'field' in values with 'field' in info.data
        in_values_pattern = r"'([^']+)' in values"
        content = re.sub(in_values_pattern, r"(info and hasattr(info, 'data') and '\1' in info.data)", content)
        
        return content
    
    def migrate_all(self) -> None:
        """Migrate all schema files in the backend."""
        print("🚀 Starting Pydantic v2 Migration")
        print("=" * 50)
        
        schema_files = self.find_schema_files()
        print(f"📁 Found {len(schema_files)} schema files to check")
        
        for file_path in schema_files:
            if self.migrate_file(file_path):
                # Count validators in the file
                with open(file_path, 'r') as f:
                    content = f.read()
                    validator_count = content.count('@field_validator(')
                    self.validators_migrated += validator_count
        
        print("=" * 50)
        print(f"✅ Migration Complete!")
        print(f"📝 Files modified: {self.files_modified}")
        print(f"🔧 Validators migrated: {self.validators_migrated}")
        
        if self.files_modified > 0:
            print("\\n🎯 Next Steps:")
            print("1. Run tests to ensure migrations work correctly")
            print("2. Check for any remaining deprecation warnings")
            print("3. Commit the migrated files")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        backend_path = sys.argv[1]
    else:
        # Default to current directory structure
        backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
    
    if not os.path.exists(backend_path):
        print(f"❌ Backend path not found: {backend_path}")
        sys.exit(1)
    
    migrator = PydanticMigrator(backend_path)
    migrator.migrate_all()


if __name__ == '__main__':
    main()
