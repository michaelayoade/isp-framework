#!/bin/bash
# ISP Framework Audit Tools Setup Script
# Installs and configures all required audit tools

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running in virtual environment
check_venv() {
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        log_warning "Not running in a virtual environment. Consider activating one."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_info "Virtual environment detected: $VIRTUAL_ENV"
    fi
}

# Install Python audit tools
install_python_tools() {
    log_info "Installing Python audit tools..."
    
    pip install --upgrade pip
    
    # Core quality tools
    pip install ruff black isort mypy
    
    # Security tools
    pip install bandit safety pip-audit detect-secrets
    
    # Testing tools
    pip install pytest pytest-cov pytest-xdist coverage vulture
    
    # Performance tools
    pip install py-spy memory-profiler
    
    # Documentation tools
    pip install pydocstyle
    
    log_success "Python audit tools installed"
}

# Install Node.js audit tools (if Node.js is available)
install_node_tools() {
    if command -v npm &> /dev/null; then
        log_info "Installing Node.js audit tools..."
        
        # Global tools
        npm install -g eslint prettier audit-ci madge
        
        # Frontend-specific tools (if frontend exists)
        if [ -d "frontend" ]; then
            cd frontend
            if [ -f "package.json" ]; then
                npm install --save-dev @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint-plugin-security
            fi
            cd ..
        fi
        
        log_success "Node.js audit tools installed"
    else
        log_warning "Node.js not found, skipping Node.js audit tools"
    fi
}

# Install system tools
install_system_tools() {
    log_info "Checking system audit tools..."
    
    # Check for Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found. Some audit features may not work."
    fi
    
    # Check for Git
    if ! command -v git &> /dev/null; then
        log_error "Git is required but not found"
        exit 1
    fi
    
    # Try to install additional tools based on OS
    if command -v apt-get &> /dev/null; then
        log_info "Installing system tools via apt..."
        sudo apt-get update
        sudo apt-get install -y pandoc wkhtmltopdf || log_warning "Could not install PDF generation tools"
    elif command -v brew &> /dev/null; then
        log_info "Installing system tools via brew..."
        brew install pandoc wkhtmltopdf || log_warning "Could not install PDF generation tools"
    else
        log_warning "Package manager not detected. Some features may not work."
    fi
}

# Setup pre-commit hooks
setup_precommit() {
    log_info "Setting up pre-commit hooks..."
    
    pip install pre-commit
    
    if [ -f ".pre-commit-config.yaml" ]; then
        pre-commit install
        pre-commit install --hook-type commit-msg
        log_success "Pre-commit hooks installed"
    else
        log_warning ".pre-commit-config.yaml not found"
    fi
}

# Create audit directories
setup_directories() {
    log_info "Creating audit directories..."
    
    mkdir -p audit-results
    mkdir -p scripts/audit
    
    # Create .secrets.baseline if it doesn't exist
    if [ ! -f ".secrets.baseline" ]; then
        echo '{}' > .secrets.baseline
        log_info "Created .secrets.baseline file"
    fi
    
    log_success "Audit directories created"
}

# Validate installation
validate_installation() {
    log_info "Validating installation..."
    
    local errors=0
    
    # Check Python tools
    for tool in ruff black isort mypy bandit safety; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool not found"
            ((errors++))
        fi
    done
    
    # Check if audit script is executable
    if [ ! -x "scripts/audit/run_comprehensive_audit.sh" ]; then
        log_error "Audit script is not executable"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "All audit tools validated successfully"
    else
        log_error "$errors validation errors found"
        exit 1
    fi
}

# Run quick test
run_quick_test() {
    log_info "Running quick audit test..."
    
    # Run a subset of checks to verify everything works
    ruff check backend/ --select E,W --quiet || log_warning "Ruff found issues (expected)"
    bandit -r backend/ -f json -o /tmp/bandit_test.json --quiet || log_warning "Bandit found issues (expected)"
    
    if [ -f "/tmp/bandit_test.json" ]; then
        rm /tmp/bandit_test.json
        log_success "Quick audit test completed"
    else
        log_error "Quick audit test failed"
    fi
}

# Main setup function
main() {
    log_info "Starting ISP Framework Audit Tools Setup"
    
    # Change to project root
    cd "$(dirname "$0")/../.."
    
    check_venv
    setup_directories
    install_python_tools
    install_node_tools
    install_system_tools
    setup_precommit
    validate_installation
    run_quick_test
    
    log_success "Audit tools setup completed successfully!"
    
    echo
    echo "🎯 Next Steps:"
    echo "1. Run a quick audit: ./scripts/audit/run_comprehensive_audit.sh --day=1"
    echo "2. Run full audit: ./scripts/audit/run_comprehensive_audit.sh"
    echo "3. Check pre-commit: pre-commit run --all-files"
    echo "4. Review documentation: docs/CODEBASE_AUDIT_STRATEGY.md"
    echo
    echo "📊 The audit system is now ready to ensure enterprise-grade code quality!"
}

# Execute main function
main "$@"
