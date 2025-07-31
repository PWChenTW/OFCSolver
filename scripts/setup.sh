#!/bin/bash

# OFC Solver Development Environment Setup Script
# This script sets up the complete development environment

set -e  # Exit on any error

echo "🎯 Setting up OFC Solver development environment..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    # Check Python version
    if ! command -v python3.11 &> /dev/null; then
        if ! command -v python3 &> /dev/null; then
            print_error "Python 3.11+ is required but not installed"
            exit 1
        else
            PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
            MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
            MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
            if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
                print_error "Python version $PYTHON_VERSION found, but 3.11+ is required"
                exit 1
            fi
            PYTHON_CMD=python3
        fi
    else
        PYTHON_CMD=python3.11
    fi
    
    # Check Poetry
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry is required but not installed. Please install from https://python-poetry.org/"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found. You'll need Docker for containerized development."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        if ! docker compose version &> /dev/null; then
            print_warning "Docker Compose not found. You'll need it for multi-container setup."
        fi
    fi
    
    print_success "Requirements check passed"
}

# Setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Configure Poetry to create virtual environment in project
    poetry config virtualenvs.in-project true
    
    # Install dependencies
    poetry install
    
    print_success "Python environment setup completed"
}

# Setup pre-commit hooks
setup_pre_commit() {
    print_status "Setting up pre-commit hooks..."
    
    poetry run pre-commit install
    poetry run pre-commit install --hook-type commit-msg
    
    print_success "Pre-commit hooks installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    mkdir -p monitoring
    mkdir -p nginx/conf.d
    mkdir -p tests/unit
    mkdir -p tests/integration
    mkdir -p tests/e2e
    mkdir -p tests/benchmarks
    
    print_success "Directories created"
}

# Setup configuration files
setup_config() {
    print_status "Setting up configuration files..."
    
    # Copy environment file if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
        print_success "Created .env file from template"
    else
        print_warning ".env file already exists, skipping"
    fi
    
    # Create basic monitoring configurations
    create_monitoring_config
    
    print_success "Configuration setup completed"
}

# Create monitoring configuration files
create_monitoring_config() {
    # Prometheus configuration
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'ofc-solver'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/health/metrics'
    scrape_interval: 30s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

    # Grafana datasource configuration
    mkdir -p monitoring/grafana/datasources
    cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Basic Nginx configuration
    mkdir -p nginx
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /health {
            proxy_pass http://app;
            access_log off;
        }
    }
}
EOF
}

# Setup Git hooks and configuration
setup_git() {
    print_status "Configuring Git..."
    
    # Set up Git hooks for better commit messages
    if [ -d .git ]; then
        # Configure Git to use conventional commits
        git config --local commit.template .gitmessage 2>/dev/null || true
        print_success "Git configuration completed"
    else
        print_warning "Not a Git repository, skipping Git setup"
    fi
}

# Run initial tests
run_initial_tests() {
    print_status "Running initial tests..."
    
    # Run code quality checks
    poetry run black --check . || {
        print_warning "Code formatting issues found. Running black..."
        poetry run black .
    }
    
    poetry run isort --check-only . || {
        print_warning "Import sorting issues found. Running isort..."
        poetry run isort .
    }
    
    # Run basic tests if they exist
    if [ -f tests/test_health.py ]; then
        poetry run pytest tests/test_health.py -v || print_warning "Some tests failed"
    fi
    
    print_success "Initial tests completed"
}

# Docker setup
setup_docker() {
    print_status "Setting up Docker environment..."
    
    if command -v docker &> /dev/null; then
        # Build Docker image
        docker build -t ofc-solver:dev --target development .
        print_success "Docker image built successfully"
        
        print_status "You can now run the application with:"
        echo "  docker-compose up -d"
    else
        print_warning "Docker not available, skipping Docker setup"
    fi
}

# Create helpful scripts
create_scripts() {
    print_status "Creating helper scripts..."
    
    # Development server script
    cat > scripts/dev-server.sh << 'EOF'
#!/bin/bash
echo "Starting OFC Solver development server..."
poetry run uvicorn src.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x scripts/dev-server.sh
    
    # Test runner script
    cat > scripts/run-tests.sh << 'EOF'
#!/bin/bash
echo "Running OFC Solver tests..."
poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
EOF
    chmod +x scripts/run-tests.sh
    
    # Code quality check script
    cat > scripts/check-quality.sh << 'EOF'
#!/bin/bash
echo "Running code quality checks..."
poetry run black --check .
poetry run isort --check-only .
poetry run flake8 src tests
poetry run mypy src
poetry run bandit -r src
EOF
    chmod +x scripts/check-quality.sh
    
    print_success "Helper scripts created"
}

# Main setup function
main() {
    echo ""
    echo "🚀 OFC Solver Development Environment Setup"
    echo "=========================================="
    echo ""
    
    check_requirements
    create_directories
    setup_python_env
    setup_config
    setup_pre_commit
    setup_git
    create_scripts
    run_initial_tests
    setup_docker
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Review and update .env file with your configuration"
    echo "  2. Start development with: ./scripts/dev-server.sh"
    echo "  3. Or use Docker: docker-compose up -d"
    echo "  4. Run tests with: ./scripts/run-tests.sh"
    echo "  5. Check code quality with: ./scripts/check-quality.sh"
    echo ""
    echo "Documentation:"
    echo "  - API docs: http://localhost:8000/api/docs"
    echo "  - Health check: http://localhost:8000/health"
    echo "  - Grafana: http://localhost:3000 (admin/admin)"
    echo ""
    print_success "Happy coding! 🎯"
}

# Run main function
main "$@"