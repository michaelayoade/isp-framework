#!/usr/bin/env python3
"""Quick fix for remaining ConfigDict import issues"""
import re
from pathlib import Path

def fix_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # Remove ConfigDict from Enum class definitions
    content = re.sub(r'class (\w+)\(([^)]+), ConfigDict\):', r'class \1(\2):', content)
    
    # Fix any other incorrect ConfigDict additions to non-pydantic imports
    content = re.sub(r'from ([^p][^y][^d][^a][^n][^t][^i][^c][^)]+), ConfigDict\)', r'from \1)', content)
    
    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

# Fix specific files
backend_path = Path('/home/ispframework/projects/isp-framework/backend/app')
fixed = []
for py_file in backend_path.rglob('*.py'):
    if fix_file(py_file):
        fixed.append(str(py_file))

print(f"Fixed {len(fixed)} files with import issues")
for f in fixed:
    print(f"  - {f}")
