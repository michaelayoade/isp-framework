#!/bin/bash
# ISP Framework Comprehensive Codebase Audit Runner
# Usage: ./scripts/audit/run_comprehensive_audit.sh [--day=1-7] [--output-dir=./audit-results]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUTPUT_DIR="${PROJECT_ROOT}/audit-results/$(date +%Y%m%d_%H%M%S)"
DAY_TO_RUN=""
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --day=*)
            DAY_TO_RUN="${1#*=}"
            shift
            ;;
        --output-dir=*)
            OUTPUT_DIR="${1#*=}"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create output directory
mkdir -p "${OUTPUT_DIR}"
cd "${PROJECT_ROOT}"

# Generate audit report header
cat > "${OUTPUT_DIR}/audit_report.md" << EOF
# ISP Framework Codebase Audit Report
**Generated**: $(date)
**Audit Strategy**: Comprehensive 7-Day Review
**Project Root**: ${PROJECT_ROOT}

## Executive Summary
EOF

# Day 1-2: Static Quality Sweep
run_day1_2() {
    log_info "Running Day 1-2: Static Quality Sweep"
    
    # 1. Lint & Style Analysis
    log_info "Running lint and style analysis..."
    
    # Backend Python
    echo "## Backend Lint Results" >> "${OUTPUT_DIR}/audit_report.md"
    if command -v ruff &> /dev/null; then
        ruff check --select ALL backend/ --output-format=json > "${OUTPUT_DIR}/ruff_results.json" 2>&1 || true
        ruff check --select ALL backend/ > "${OUTPUT_DIR}/ruff_results.txt" 2>&1 || true
        echo "- Ruff analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
    else
        log_warning "ruff not found, skipping Python linting"
    fi
    
    if command -v isort &> /dev/null; then
        isort --check-only --diff backend/ > "${OUTPUT_DIR}/isort_results.txt" 2>&1 || true
        echo "- Import sorting analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
    fi
    
    if command -v black &> /dev/null; then
        black --check backend/ > "${OUTPUT_DIR}/black_results.txt" 2>&1 || true
        echo "- Code formatting analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
    fi
    
    # Frontend TypeScript (if exists)
    if [ -f "frontend/package.json" ]; then
        echo "## Frontend Lint Results" >> "${OUTPUT_DIR}/audit_report.md"
        cd frontend
        if [ -f "package.json" ] && command -v npm &> /dev/null; then
            npm run lint > "${OUTPUT_DIR}/frontend_lint.txt" 2>&1 || true
            npm run type-check > "${OUTPUT_DIR}/frontend_typecheck.txt" 2>&1 || true
            echo "- TypeScript linting and type checking completed" >> "${OUTPUT_DIR}/audit_report.md"
        fi
        cd ..
    fi
    
    # 2. Type Correctness
    log_info "Running type correctness analysis..."
    echo "## Type Analysis Results" >> "${OUTPUT_DIR}/audit_report.md"
    
    if command -v mypy &> /dev/null; then
        mypy --strict --no-warn-unused-ignores backend/ > "${OUTPUT_DIR}/mypy_results.txt" 2>&1 || true
        echo "- MyPy strict type checking completed" >> "${OUTPUT_DIR}/audit_report.md"
    else
        log_warning "mypy not found, skipping type checking"
    fi
    
    # 3. Dead Code & Stubs
    log_info "Running dead code analysis..."
    echo "## Dead Code Analysis" >> "${OUTPUT_DIR}/audit_report.md"
    
    if command -v vulture &> /dev/null; then
        vulture backend/ --min-confidence 80 > "${OUTPUT_DIR}/vulture_results.txt" 2>&1 || true
        echo "- Dead code analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
    fi
    
    # TODO/FIXME analysis
    grep -r "TODO\|FIXME\|XXX\|HACK" backend/ frontend/ > "${OUTPUT_DIR}/todo_analysis.txt" 2>&1 || true
    echo "- TODO/FIXME analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
    
    log_success "Day 1-2 analysis completed"
}

# Day 2-3: Security & Dependencies
run_day2_3() {
    log_info "Running Day 2-3: Security & Dependencies"
    
    # 4. Supply-Chain Security
    log_info "Running supply-chain security analysis..."
    echo "## Security Analysis Results" >> "${OUTPUT_DIR}/audit_report.md"
    
    if command -v safety &> /dev/null; then
        safety check --json > "${OUTPUT_DIR}/safety_results.json" 2>&1 || true
        safety check > "${OUTPUT_DIR}/safety_results.txt" 2>&1 || true
        echo "- Python dependency vulnerability scan completed" >> "${OUTPUT_DIR}/audit_report.md"
    fi
    
    if command -v pip-audit &> /dev/null; then
        pip-audit --format=json > "${OUTPUT_DIR}/pip_audit_results.json" 2>&1 || true
        pip-audit > "${OUTPUT_DIR}/pip_audit_results.txt" 2>&1 || true
        echo "- Pip audit completed" >> "${OUTPUT_DIR}/audit_report.md"
    fi
    
    # Frontend dependencies
    if [ -f "frontend/package.json" ]; then
        cd frontend
        if command -v npm &> /dev/null; then
            npm audit --audit-level=moderate > "${OUTPUT_DIR}/npm_audit_results.txt" 2>&1 || true
            echo "- NPM dependency audit completed" >> "${OUTPUT_DIR}/audit_report.md"
        fi
        cd ..
    fi
    
    # 5. Code-Level Security
    log_info "Running code-level security analysis..."
    
    if command -v bandit &> /dev/null; then
        bandit -r backend/ -f json > "${OUTPUT_DIR}/bandit_results.json" 2>&1 || true
        bandit -r backend/ > "${OUTPUT_DIR}/bandit_results.txt" 2>&1 || true
        echo "- Python security analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
    fi
    
    # 6. Secrets Detection
    log_info "Running secrets detection..."
    
    if command -v detect-secrets &> /dev/null; then
        detect-secrets scan --all-files > "${OUTPUT_DIR}/secrets_scan.json" 2>&1 || true
        echo "- Secrets detection completed" >> "${OUTPUT_DIR}/audit_report.md"
    fi
    
    log_success "Day 2-3 analysis completed"
}

# Day 3-4: Test & Coverage Health
run_day3_4() {
    log_info "Running Day 3-4: Test & Coverage Health"
    
    echo "## Test & Coverage Analysis" >> "${OUTPUT_DIR}/audit_report.md"
    
    # 7. Test Inventory & Coverage
    log_info "Running test coverage analysis..."
    
    # Backend tests
    if [ -f "backend/pytest.ini" ]; then
        cd backend
        if command -v pytest &> /dev/null; then
            pytest --collect-only --quiet > "${OUTPUT_DIR}/test_inventory.txt" 2>&1 || true
            pytest --cov=app --cov-report=html:"${OUTPUT_DIR}/coverage_html" --cov-report=json:"${OUTPUT_DIR}/coverage.json" > "${OUTPUT_DIR}/test_results.txt" 2>&1 || true
            echo "- Backend test coverage analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
        fi
        cd ..
    fi
    
    # Frontend tests
    if [ -f "frontend/package.json" ]; then
        cd frontend
        if command -v npm &> /dev/null; then
            npm run test:coverage > "${OUTPUT_DIR}/frontend_test_results.txt" 2>&1 || true
            echo "- Frontend test coverage analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
        fi
        cd ..
    fi
    
    # 9. Test Reliability
    log_info "Running test reliability analysis..."
    
    if [ -f "backend/pytest.ini" ]; then
        cd backend
        pytest -n auto --reruns 2 --tb=short > "${OUTPUT_DIR}/test_reliability.txt" 2>&1 || true
        cd ..
    fi
    
    log_success "Day 3-4 analysis completed"
}

# Day 4-5: Runtime & Performance
run_day4_5() {
    log_info "Running Day 4-5: Runtime & Performance"
    
    echo "## Performance Analysis" >> "${OUTPUT_DIR}/audit_report.md"
    
    # 11. Database & Cache Audit
    log_info "Running database analysis..."
    
    # Check for common performance issues
    grep -r "SELECT.*\*" backend/ > "${OUTPUT_DIR}/select_star_queries.txt" 2>&1 || true
    grep -r "\.all()" backend/ > "${OUTPUT_DIR}/potential_n_plus_1.txt" 2>&1 || true
    echo "- Database query pattern analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
    
    log_success "Day 4-5 analysis completed"
}

# Day 5-6: Architecture & Documentation
run_day5_6() {
    log_info "Running Day 5-6: Architecture & Documentation"
    
    echo "## Architecture & Documentation Analysis" >> "${OUTPUT_DIR}/audit_report.md"
    
    # 13. Dependency Analysis
    log_info "Running dependency analysis..."
    
    # Python imports analysis
    find backend/ -name "*.py" -exec grep -l "^import\|^from" {} \; > "${OUTPUT_DIR}/import_files.txt" 2>&1 || true
    
    # Circular dependency detection
    if command -v madge &> /dev/null && [ -d "frontend/src" ]; then
        cd frontend
        madge --circular src/ > "${OUTPUT_DIR}/circular_dependencies.txt" 2>&1 || true
        cd ..
    fi
    
    # 15. Documentation Coverage
    log_info "Running documentation analysis..."
    
    if command -v pydocstyle &> /dev/null; then
        pydocstyle backend/app/ > "${OUTPUT_DIR}/docstring_analysis.txt" 2>&1 || true
        echo "- Python docstring analysis completed" >> "${OUTPUT_DIR}/audit_report.md"
    fi
    
    # Find Python files without docstrings
    find backend/ -name "*.py" -exec grep -L '"""' {} \; > "${OUTPUT_DIR}/missing_docstrings.txt" 2>&1 || true
    
    log_success "Day 5-6 analysis completed"
}

# Generate summary report
generate_summary() {
    log_info "Generating audit summary..."
    
    cat >> "${OUTPUT_DIR}/audit_report.md" << EOF

## Summary Statistics

### Files Analyzed
- Python files: $(find backend/ -name "*.py" | wc -l)
- TypeScript files: $(find frontend/ -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l || echo "0")
- Total lines of code: $(find backend/ frontend/ -name "*.py" -o -name "*.ts" -o -name "*.tsx" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo "Unknown")

### Issues Found
- Lint issues: $(wc -l < "${OUTPUT_DIR}/ruff_results.txt" 2>/dev/null || echo "0")
- Type errors: $(grep -c "error:" "${OUTPUT_DIR}/mypy_results.txt" 2>/dev/null || echo "0")
- Security issues: $(grep -c "Issue:" "${OUTPUT_DIR}/bandit_results.txt" 2>/dev/null || echo "0")
- TODO items: $(wc -l < "${OUTPUT_DIR}/todo_analysis.txt" 2>/dev/null || echo "0")

### Recommendations
1. Address critical security vulnerabilities immediately
2. Fix type errors to improve code reliability
3. Resolve high-priority lint issues
4. Improve test coverage in identified gaps
5. Update documentation for missing docstrings

### Next Steps
1. Review detailed results in individual files
2. Prioritize fixes based on risk assessment
3. Update CI/CD pipeline with quality gates
4. Schedule follow-up audit in 3 months

**Audit completed at**: $(date)
EOF

    log_success "Audit summary generated"
}

# Main execution
main() {
    log_info "Starting ISP Framework Comprehensive Codebase Audit"
    log_info "Output directory: ${OUTPUT_DIR}"
    
    if [ -n "${DAY_TO_RUN}" ]; then
        case "${DAY_TO_RUN}" in
            1|2)
                run_day1_2
                ;;
            3|4)
                run_day2_3
                run_day3_4
                ;;
            5|6)
                run_day4_5
                run_day5_6
                ;;
            7)
                generate_summary
                ;;
            *)
                log_error "Invalid day specified. Use 1-7."
                exit 1
                ;;
        esac
    else
        # Run full audit
        run_day1_2
        run_day2_3
        run_day3_4
        run_day4_5
        run_day5_6
        generate_summary
    fi
    
    log_success "Audit completed successfully!"
    log_info "Results available in: ${OUTPUT_DIR}"
    log_info "Main report: ${OUTPUT_DIR}/audit_report.md"
}

# Execute main function
main "$@"
