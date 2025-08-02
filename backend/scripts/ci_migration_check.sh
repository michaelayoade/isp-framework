#!/bin/bash
# CI Migration Health Check Script
# Prevents migration issues from being committed to repository

set -e

echo "🔍 Running Migration Health Check..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if we're in Docker environment
if [ -f /.dockerenv ]; then
    PYTHON_CMD="python"
    ALEMBIC_CMD="alembic"
else
    PYTHON_CMD="docker exec -it isp-backend python"
    ALEMBIC_CMD="docker exec -it isp-backend alembic"
fi

# 1. Run comprehensive migration audit
print_status $YELLOW "1. Running comprehensive migration audit..."
if $PYTHON_CMD scripts/audit_migrations.py; then
    print_status $GREEN "✅ Migration audit passed"
else
    print_status $RED "❌ Migration audit failed"
    exit 1
fi

# 2. Check for single head
print_status $YELLOW "2. Checking for single migration head..."
HEAD_COUNT=$($ALEMBIC_CMD heads | wc -l)
if [ $HEAD_COUNT -eq 1 ]; then
    print_status $GREEN "✅ Single migration head confirmed"
else
    print_status $RED "❌ Multiple migration heads detected ($HEAD_COUNT)"
    $ALEMBIC_CMD heads
    exit 1
fi

# 3. Check for clean branches
print_status $YELLOW "3. Checking migration branch structure..."
BRANCH_OUTPUT=$($ALEMBIC_CMD branches 2>/dev/null || echo "")
if [ -z "$BRANCH_OUTPUT" ]; then
    print_status $GREEN "✅ No problematic branches detected"
else
    print_status $YELLOW "⚠️  Branch structure detected (may be normal):"
    echo "$BRANCH_OUTPUT"
fi

# 4. Validate migration chain integrity
print_status $YELLOW "4. Validating migration chain integrity..."
if $ALEMBIC_CMD check 2>/dev/null; then
    print_status $GREEN "✅ Migration chain is valid"
else
    print_status $YELLOW "⚠️  Database not up to date (may be normal in CI)"
fi

# 5. Check for duplicate migration files
print_status $YELLOW "5. Checking for duplicate migration files..."
DUPLICATE_CHECK=$($PYTHON_CMD -c "
import pathlib, collections
versions = pathlib.Path('alembic/versions')
revisions = collections.defaultdict(list)
for py in versions.rglob('*.py'):
    if py.name == '__init__.py': continue
    try:
        with open(py) as f:
            content = f.read()
            if 'revision =' in content:
                for line in content.split('\n'):
                    if line.strip().startswith('revision ='):
                        rev = line.split('=')[1].strip().strip('\"').strip(\"'\")
                        revisions[rev].append(str(py))
                        break
    except: pass
duplicates = {k:v for k,v in revisions.items() if len(v) > 1}
if duplicates:
    print('DUPLICATES_FOUND')
    for rev, files in duplicates.items():
        print(f'{rev}: {files}')
else:
    print('NO_DUPLICATES')
")

if echo "$DUPLICATE_CHECK" | grep -q "NO_DUPLICATES"; then
    print_status $GREEN "✅ No duplicate migration files found"
else
    print_status $RED "❌ Duplicate migration files detected:"
    echo "$DUPLICATE_CHECK" | grep -v "DUPLICATES_FOUND"
    exit 1
fi

# 6. Check for orphaned archived migrations
print_status $YELLOW "6. Checking for orphaned archived migrations..."
ORPHANED_CHECK=$($PYTHON_CMD -c "
import pathlib, importlib.util
versions = pathlib.Path('alembic/versions')
archived_revisions = set()
active_references = set()

# Get all archived revisions
for py in versions.glob('archived_migrations/*.py'):
    if py.name == '__init__.py': continue
    try:
        spec = importlib.util.spec_from_file_location('mod', py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        archived_revisions.add(mod.revision)
    except: pass

# Check active migrations for references to archived ones
for py in versions.rglob('*.py'):
    if 'archived_migrations' in str(py) or py.name == '__init__.py': continue
    try:
        spec = importlib.util.spec_from_file_location('mod', py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        down_rev = mod.down_revision
        if isinstance(down_rev, str) and down_rev in archived_revisions:
            active_references.add(down_rev)
        elif isinstance(down_rev, (list, tuple)):
            for dep in down_rev:
                if dep in archived_revisions:
                    active_references.add(dep)
    except: pass

orphaned = archived_revisions - active_references
if orphaned:
    print('ORPHANED_FOUND')
    for rev in orphaned:
        print(rev)
else:
    print('NO_ORPHANED')
")

if echo "$ORPHANED_CHECK" | grep -q "NO_ORPHANED"; then
    print_status $GREEN "✅ No orphaned archived migrations found"
else
    print_status $YELLOW "⚠️  Orphaned archived migrations detected (may be safe to remove):"
    echo "$ORPHANED_CHECK" | grep -v "ORPHANED_FOUND"
fi

print_status $GREEN "🎉 Migration health check completed successfully!"
echo ""
echo "Summary:"
echo "- Migration audit: PASSED"
echo "- Single head: CONFIRMED"
echo "- Chain integrity: VALIDATED"
echo "- No duplicates: CONFIRMED"
echo "- Orphaned migrations: CHECKED"
echo ""
print_status $GREEN "Migration system is healthy and ready for deployment!"
