"""
Application configuration management using Pydantic settings.
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, validator


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    host: str = "localhost"
    port: int = 5432
    name: str = "ofc_solver"
    user: str = "postgres"
    password: str = ""

    # Connection pool settings
    min_connections: int = 5
    max_connections: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30

    @property
    def url(self) -> str:
        """Get the database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None

    # Connection pool settings
    max_connections: int = 20
    retry_on_timeout: bool = True
    socket_timeout: int = 5

    @property
    def url(self) -> str:
        """Get the Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.database}"

    class Config:
        env_prefix = "REDIS_"


class CelerySettings(BaseSettings):
    """Celery configuration settings."""

    broker_url: str = "redis://localhost:6379/1"
    result_backend: str = "redis://localhost:6379/2"

    # Task settings
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = ["json"]
    timezone: str = "UTC"
    enable_utc: bool = True

    # Worker settings
    worker_prefetch_multiplier: int = 1
    task_acks_late: bool = True
    worker_max_tasks_per_child: int = 1000

    class Config:
        env_prefix = "CELERY_"


class SolverSettings(BaseSettings):
    """Solver engine configuration settings."""

    # Calculation settings
    max_calculation_time_seconds: int = 300
    default_monte_carlo_samples: int = 100000
    max_tree_depth: int = 5

    # Performance settings
    max_parallel_workers: int = os.cpu_count() or 4
    calculation_timeout_seconds: int = 600
    memory_limit_mb: int = 1024

    # Cache settings
    position_cache_ttl_hours: int = 24
    strategy_cache_size: int = 10000

    class Config:
        env_prefix = "SOLVER_"


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Rate limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10

    # CORS settings
    allowed_origins: List[str] = ["*"]
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]

    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    class Config:
        env_prefix = "SECURITY_"


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # File logging
    log_file: str = "logs/app.log"
    max_file_size_mb: int = 100
    backup_count: int = 5

    # Structured logging
    use_json_format: bool = False
    include_trace_id: bool = True

    class Config:
        env_prefix = "LOG_"


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""

    # Prometheus metrics
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Health checks
    health_check_interval_seconds: int = 30
    database_timeout_seconds: int = 5
    redis_timeout_seconds: int = 3

    # Alerting
    enable_alerts: bool = False
    alert_webhook_url: Optional[str] = None

    class Config:
        env_prefix = "MONITORING_"


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: str = "development"
    debug: bool = True

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Service settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()
    solver: SolverSettings = SolverSettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    monitoring: MonitoringSettings = MonitoringSettings()

    @validator("environment")
    def validate_environment(cls, v):
        if v not in ["development", "testing", "staging", "production"]:
            raise ValueError(
                "Environment must be one of: development, testing, staging, production"
            )
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings."""
    return settings
