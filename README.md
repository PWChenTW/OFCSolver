# OFC Solver System

A comprehensive Open Face Chinese (OFC) Poker solver implementing advanced Game Theory Optimal (GTO) calculations with domain-driven design principles.

## 🎯 Overview

The OFC Solver System is designed to provide optimal strategy calculations for Open Face Chinese Poker, featuring:

- **Advanced GTO Calculations**: Monte Carlo simulations and exhaustive analysis
- **Real-time Analysis**: Fast strategy recommendations with confidence intervals
- **Training Platform**: Interactive scenarios for skill improvement
- **Performance Monitoring**: Comprehensive metrics and observability
- **Scalable Architecture**: Clean domain-driven design with microservices support

## 🏗️ Architecture

The system follows Domain-Driven Design (DDD) principles with a layered architecture:

```
src/
├── domain/           # Core business logic (entities, value objects, services)
├── application/      # Application services (commands, queries, handlers)
├── infrastructure/   # Technical implementations (database, web, external services)
└── presentation/     # API endpoints and user interfaces
```

### Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Databases**: PostgreSQL (primary), Redis (cache), ClickHouse (analytics)
- **Message Queue**: RabbitMQ with Celery
- **Computing**: NumPy, SciPy for mathematical operations
- **Monitoring**: Prometheus, Grafana
- **Containerization**: Docker, Docker Compose, Kubernetes

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry (dependency management)
- Docker & Docker Compose
- Git

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/ofc-solver.git
cd ofc-solver

# Run automated setup
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. Environment Configuration

```bash
# Copy and edit environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Development Environment

#### Option A: Docker Compose (Recommended)
```bash
docker-compose up -d
```

#### Option B: Local Development
```bash
# Start dependencies
docker-compose up -d postgres redis rabbitmq

# Run application locally
poetry run uvicorn src.main:create_app --factory --reload
```

### 4. Access Services

- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **RabbitMQ Management**: http://localhost:15672 (admin/admin)

## 📖 API Usage

### Game Management

```python
import httpx

# Create a new game
response = httpx.post("http://localhost:8000/api/v1/games/", json={
    "player_count": 2,
    "rules_variant": "standard"
})
game = response.json()

# Get game state
response = httpx.get(f"http://localhost:8000/api/v1/games/{game['id']}/state")
state = response.json()
```

### Strategy Analysis

```python
# Calculate optimal strategy
analysis_request = {
    "position": {
        "players_hands": {"0": ["As", "Kh"], "1": ["Qd", "Jc"]},
        "remaining_cards": ["2s", "3h", "4d", ...],
        "current_player": 0,
        "round_number": 1
    },
    "calculation_mode": "standard",
    "max_calculation_time_seconds": 60
}

response = httpx.post(
    "http://localhost:8000/api/v1/analysis/calculate-strategy",
    json=analysis_request
)
strategy = response.json()
```

### Training Sessions

```python
# Start training session
response = httpx.post("http://localhost:8000/api/v1/training/sessions", json={
    "difficulty_level": "intermediate",
    "scenario_type": "general",
    "session_length": 10
})
session = response.json()

# Submit answer
response = httpx.post(
    f"http://localhost:8000/api/v1/training/sessions/{session['session_id']}/answer",
    json={
        "selected_move": "place_As_top_1",
        "time_taken_seconds": 45
    }
)
feedback = response.json()
```

## 🧪 Development

### Code Quality

The project uses automated code quality tools:

```bash
# Format code
poetry run black .
poetry run isort .

# Lint code
poetry run flake8 src tests
poetry run mypy src

# Security check
poetry run bandit -r src

# Run all quality checks
./scripts/check-quality.sh
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test categories
poetry run pytest tests/unit -m unit
poetry run pytest tests/integration -m integration
poetry run pytest tests/e2e -m e2e

# Use helper script
./scripts/run-tests.sh
```

### Pre-commit Hooks

Pre-commit hooks are automatically installed during setup:

```bash
# Manual installation
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```

## 📊 Monitoring

### Health Checks

The system provides comprehensive health monitoring:

- **Liveness**: `/health/liveness`
- **Readiness**: `/health/readiness` 
- **Full Health**: `/health/`
- **Metrics**: `/health/metrics`

### Prometheus Metrics

Key metrics tracked:

- Request rates and response times
- Solver calculation performance
- Cache hit rates
- Database connection pool status
- Memory and CPU usage

### Grafana Dashboards

Pre-configured dashboards for:

- Application performance
- Solver engine metrics
- Database performance
- System resource usage

## 🔧 Configuration

### Environment Variables

Key configuration options:

```bash
# Application
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ofc_solver
DB_USER=postgres
DB_PASSWORD=your_password

# Solver Settings
SOLVER_MAX_CALCULATION_TIME_SECONDS=300
SOLVER_DEFAULT_MONTE_CARLO_SAMPLES=100000
SOLVER_MAX_PARALLEL_WORKERS=4

# Security
SECURITY_SECRET_KEY=your-secret-key-here
SECURITY_RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### Solver Configuration

Customize solver behavior:

```python
from src.config import settings

# Adjust calculation parameters
settings.solver.max_calculation_time_seconds = 600
settings.solver.default_monte_carlo_samples = 200000
settings.solver.max_tree_depth = 7
```

## 🚀 Deployment

### Production Docker Image

```bash
# Build production image
docker build -t ofc-solver:latest --target production .

# Run with production settings
docker run -p 8000:8000 -e ENVIRONMENT=production ofc-solver:latest
```

### Kubernetes

Helm charts and Kubernetes manifests are provided:

```bash
# Deploy with Helm
helm install ofc-solver ./charts/ofc-solver

# Or use kubectl
kubectl apply -f k8s/
```

### CI/CD

GitHub Actions pipeline includes:

- Code quality checks
- Automated testing
- Security scanning
- Docker image building
- Deployment to staging/production

## 📚 Documentation

### API Documentation

- **OpenAPI Spec**: Available at `/api/docs` when running
- **ReDoc**: Alternative docs at `/api/redoc`

### Domain Documentation

Detailed domain model documentation in `docs/domain/`:
- Entity relationships
- Business rules
- Domain events
- Value objects

### Architecture Decision Records

ADRs document key architectural decisions in `docs/adr/`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run quality checks: `./scripts/check-quality.sh`
5. Run tests: `./scripts/run-tests.sh`
6. Commit with conventional commits: `feat: add amazing feature`
7. Push and create a Pull Request

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/modifications
- `chore:` Maintenance tasks

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Open Face Chinese Poker community
- Game theory and poker strategy researchers
- Open source contributors

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: dev@ofcsolver.com

---

**Made with ❤️ for the poker community**