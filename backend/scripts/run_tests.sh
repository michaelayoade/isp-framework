#!/bin/bash
# Docker-native test runner for ISP Framework backend
# This script provides a unified interface for running tests inside Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
COVERAGE=false
PARALLEL=false
MARKERS=""
VERBOSE=false
CLEAN=false

# Help function
show_help() {
    echo "Docker-native test runner for ISP Framework backend"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --coverage      Run tests with coverage report"
    echo "  -p, --parallel      Run tests in parallel using pytest-xdist"
    echo "  -m, --markers       Run only tests with specific markers (e.g., 'unit', 'not integration')"
    echo "  -v, --verbose       Verbose output"
    echo "  --clean             Clean test artifacts before running"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Run all tests"
    echo "  $0 -c                       # Run with coverage"
    echo "  $0 -p -c                    # Run in parallel with coverage"
    echo "  $0 -m 'unit'                # Run only unit tests"
    echo "  $0 -m 'not integration'     # Skip integration tests"
    echo "  $0 -m 'rbac or device'      # Run RBAC and device tests"
    echo "  $0 --clean -c               # Clean artifacts and run with coverage"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to check if Docker services are running
check_services() {
    echo -e "${BLUE}Checking Docker services...${NC}"
    
    if ! docker-compose ps | grep -q "Up"; then
        echo -e "${YELLOW}Starting Docker services...${NC}"
        docker-compose up -d postgres redis backend
        
        # Wait for services to be ready
        echo -e "${BLUE}Waiting for services to be ready...${NC}"
        sleep 10
        
        # Check if backend is healthy
        for i in {1..30}; do
            if docker-compose exec backend curl -f http://localhost:8000/health >/dev/null 2>&1; then
                echo -e "${GREEN}Backend service is ready${NC}"
                break
            fi
            if [ $i -eq 30 ]; then
                echo -e "${RED}Backend service failed to start${NC}"
                exit 1
            fi
            sleep 2
        done
    else
        echo -e "${GREEN}Docker services are running${NC}"
    fi
}

# Function to run database migrations
run_migrations() {
    echo -e "${BLUE}Running database migrations...${NC}"
    docker-compose exec backend alembic upgrade head
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Migrations completed successfully${NC}"
    else
        echo -e "${RED}Migration failed${NC}"
        exit 1
    fi
}

# Function to clean test artifacts
clean_artifacts() {
    if [ "$CLEAN" = true ]; then
        echo -e "${BLUE}Cleaning test artifacts...${NC}"
        docker-compose exec backend rm -rf .pytest_cache/ .coverage htmlcov/ test-results/
        echo -e "${GREEN}Test artifacts cleaned${NC}"
    fi
}

# Function to build pytest command
build_pytest_command() {
    local cmd="pytest"
    
    # Add coverage options
    if [ "$COVERAGE" = true ]; then
        cmd="$cmd --cov=app --cov-report=term-missing --cov-report=html:htmlcov"
    fi
    
    # Add parallel execution
    if [ "$PARALLEL" = true ]; then
        cmd="$cmd -n auto"
    fi
    
    # Add markers
    if [ -n "$MARKERS" ]; then
        cmd="$cmd -m '$MARKERS'"
    fi
    
    # Add verbose output
    if [ "$VERBOSE" = true ]; then
        cmd="$cmd -v"
    else
        cmd="$cmd -q"
    fi
    
    echo "$cmd"
}

# Function to run tests
run_tests() {
    local pytest_cmd=$(build_pytest_command)
    
    echo -e "${BLUE}Running tests with command: ${pytest_cmd}${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Execute tests inside Docker container
    docker-compose exec backend bash -c "$pytest_cmd"
    local exit_code=$?
    
    echo -e "${BLUE}========================================${NC}"
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        
        # Show coverage summary if coverage was enabled
        if [ "$COVERAGE" = true ]; then
            echo -e "${BLUE}Coverage Summary:${NC}"
            docker-compose exec backend coverage report --show-missing
            echo -e "${YELLOW}HTML coverage report generated in htmlcov/${NC}"
        fi
    else
        echo -e "${RED}Some tests failed (exit code: $exit_code)${NC}"
        exit $exit_code
    fi
}

# Function to show test statistics
show_stats() {
    echo -e "${BLUE}Test Statistics:${NC}"
    docker-compose exec backend bash -c "find tests/ -name '*.py' -not -name '__*' | wc -l | xargs echo 'Test files:'"
    docker-compose exec backend bash -c "grep -r 'def test_' tests/ | wc -l | xargs echo 'Test functions:'"
    docker-compose exec backend bash -c "grep -r '@pytest.mark' tests/ | cut -d: -f2 | grep -o '@pytest.mark.[a-zA-Z_]*' | sort | uniq -c | sort -nr"
}

# Main execution
main() {
    echo -e "${GREEN}ISP Framework Docker-Native Test Runner${NC}"
    echo -e "${BLUE}=====================================${NC}"
    
    # Check and start services
    check_services
    
    # Run migrations to ensure test database is up to date
    run_migrations
    
    # Clean artifacts if requested
    clean_artifacts
    
    # Show test statistics
    show_stats
    
    # Run tests
    run_tests
    
    echo -e "${GREEN}Test execution completed!${NC}"
}

# Execute main function
main
