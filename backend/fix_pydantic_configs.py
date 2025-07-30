#!/usr/bin/env python3
"""
Script to systematically fix Pydantic V1 class Config to V2 model_config = ConfigDict
"""
import os
import re
from pathlib import Path

def fix_config_in_file(file_path):
    """Fix Pydantic Config classes in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match class Config: with orm_mode = True
    config_pattern = r'    class Config:\s*\n        orm_mode = True'
    replacement = '    model_config = ConfigDict(from_attributes=True)'
    
    content = re.sub(config_pattern, replacement, content)
    
    # Pattern to match class Config: with other simple configurations
    # This handles cases like arbitrary_types_allowed = True, etc.
    complex_config_pattern = r'    class Config:\s*\n((?:        \w+.*\n)*)'
    
    def replace_complex_config(match):
        config_lines = match.group(1).strip()
        if not config_lines:
            return '    model_config = ConfigDict()'
        
        # Parse individual config lines
        config_dict_items = []
        for line in config_lines.split('\n'):
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Convert known V1 keys to V2
                if key == 'orm_mode':
                    config_dict_items.append('from_attributes=True')
                elif key == 'arbitrary_types_allowed':
                    config_dict_items.append(f'arbitrary_types_allowed={value}')
                elif key == 'allow_population_by_field_name':
                    config_dict_items.append(f'populate_by_name={value}')
                elif key == 'use_enum_values':
                    config_dict_items.append(f'use_enum_values={value}')
                else:
                    # Keep other configs as-is for now
                    config_dict_items.append(f'{key}={value}')
        
        if config_dict_items:
            return f'    model_config = ConfigDict({", ".join(config_dict_items)})'
        else:
            return '    model_config = ConfigDict()'
    
    content = re.sub(complex_config_pattern, replace_complex_config, content)
    
    # Check if ConfigDict import is needed and missing
    if 'model_config = ConfigDict' in content and 'ConfigDict' not in content.split('model_config')[0]:
        # Add ConfigDict to existing pydantic import
        import_pattern = r'from pydantic import ([^)]+)'
        def add_configdict(match):
            imports = match.group(1)
            if 'ConfigDict' not in imports:
                return f'from pydantic import {imports}, ConfigDict'
            return match.group(0)
        
        content = re.sub(import_pattern, add_configdict, content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all Python files in the backend."""
    backend_path = Path('/home/ispframework/projects/isp-framework/backend/app')
    
    fixed_files = []
    for py_file in backend_path.rglob('*.py'):
        if fix_config_in_file(py_file):
            fixed_files.append(str(py_file))
    
    print(f"Fixed {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  - {file}")

if __name__ == '__main__':
    main()
