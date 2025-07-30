#!/usr/bin/env python3
"""Fix remaining ConfigDict import issues"""
import re
from pathlib import Path

def fix_configdict_imports(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # Check if file uses model_config = ConfigDict but doesn't import ConfigDict
    if 'model_config = ConfigDict' in content and 'ConfigDict' not in content.split('model_config')[0]:
        # Add ConfigDict to existing pydantic import
        pydantic_import_pattern = r'from pydantic import ([^)]+)'
        
        def add_configdict(match):
            imports = match.group(1)
            if 'ConfigDict' not in imports:
                return f'from pydantic import {imports}, ConfigDict'
            return match.group(0)
        
        content = re.sub(pydantic_import_pattern, add_configdict, content)
    
    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

# Fix all Python files
backend_path = Path('/home/ispframework/projects/isp-framework/backend/app')
fixed = []
for py_file in backend_path.rglob('*.py'):
    if fix_configdict_imports(py_file):
        fixed.append(str(py_file))

print(f"Fixed ConfigDict imports in {len(fixed)} files")
for f in fixed:
    print(f"  - {f}")
