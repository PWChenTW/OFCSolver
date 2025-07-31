import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Game(Base):
    """Game entity for OFC games."""

    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_count = Column(Integer, nullable=False)
    rules_variant = Column(String(50), nullable=False, default="standard")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    final_scores = Column(JSON, nullable=True)

    # Relationships
    positions = relationship(
        "Position", back_populates="game", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("player_count BETWEEN 2 AND 4", name="valid_player_count"),
        CheckConstraint(
            "status IN ('active', 'completed', 'paused', 'cancelled')",
            name="valid_status",
        ),
        Index("idx_games_created_at", "created_at"),
        Index("idx_games_status", "status"),
        Index("idx_games_completed_at", "completed_at"),
    )


class Position(Base):
    """Position entity for game states."""

    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(
        UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    round_number = Column(Integer, nullable=False)
    current_player = Column(Integer, nullable=False)
    players_hands = Column(JSON, nullable=False)
    remaining_cards = Column(JSON, nullable=False)  # Array of integers
    position_hash = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    game = relationship("Game", back_populates="positions")
    analysis_results = relationship(
        "AnalysisResult", back_populates="position", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("round_number > 0", name="valid_round_number"),
        CheckConstraint("current_player >= 0", name="valid_current_player"),
        Index("idx_positions_game_id", "game_id"),
        Index("idx_positions_hash", "position_hash"),
        Index("idx_positions_created_at", "created_at"),
        Index(
            "idx_positions_game_round_player",
            "game_id",
            "round_number",
            "current_player",
            unique=True,
        ),
    )


class AnalysisResult(Base):
    """Analysis result entity for position calculations."""

    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id = Column(
        UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    optimal_strategy = Column(JSON, nullable=False)
    expected_value = Column(Numeric(10, 6), nullable=False)
    calculation_method = Column(String(20), nullable=False)
    calculation_time_ms = Column(Integer, nullable=False)
    confidence_level = Column(Numeric(4, 3), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    position = relationship("Position", back_populates="analysis_results")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "calculation_method IN ('heuristic', 'monte_carlo', 'exhaustive', 'hybrid')",
            name="valid_calculation_method",
        ),
        CheckConstraint("calculation_time_ms >= 0", name="valid_calculation_time"),
        CheckConstraint(
            "confidence_level BETWEEN 0 AND 1", name="valid_confidence_level"
        ),
        Index("idx_analysis_position_id", "position_id"),
        Index("idx_analysis_method", "calculation_method"),
        Index("idx_analysis_created_at", "created_at"),
    )


class TrainingSession(Base):
    """Training session entity."""

    __tablename__ = "training_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # NULL for anonymous sessions
    difficulty_level = Column(String(20), nullable=False, default="intermediate")
    scenario_type = Column(String(30), nullable=False, default="general")
    total_scenarios = Column(Integer, nullable=False)
    completed_scenarios = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="active")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    performance_metrics = relationship(
        "PerformanceMetric", back_populates="session", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')",
            name="valid_difficulty",
        ),
        CheckConstraint(
            "status IN ('active', 'completed', 'paused', 'abandoned')",
            name="valid_session_status",
        ),
        CheckConstraint("total_scenarios > 0", name="valid_total_scenarios"),
        CheckConstraint("completed_scenarios >= 0", name="valid_completed_scenarios"),
        CheckConstraint(
            "completed_scenarios <= total_scenarios", name="completed_not_exceed_total"
        ),
        Index("idx_training_user_id", "user_id"),
        Index("idx_training_status", "status"),
        Index("idx_training_started_at", "started_at"),
    )


class PerformanceMetric(Base):
    """Performance metric entity for training sessions."""

    __tablename__ = "performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("training_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    scenario_id = Column(String(100), nullable=False)
    user_answer = Column(String(200), nullable=True)
    optimal_answer = Column(String(200), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    ev_difference = Column(Numeric(8, 4), nullable=True)
    decision_time_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("TrainingSession", back_populates="performance_metrics")

    # Constraints
    __table_args__ = (
        CheckConstraint("decision_time_seconds >= 0", name="valid_decision_time"),
        Index("idx_performance_session_id", "session_id"),
        Index("idx_performance_created_at", "created_at"),
        Index("idx_performance_is_correct", "is_correct"),
    )


class SystemMetric(Base):
    """System metric entity for monitoring."""

    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(15, 6), nullable=False)
    metric_type = Column(String(20), nullable=False, default="gauge")
    tags = Column(JSON, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "metric_type IN ('counter', 'gauge', 'histogram', 'summary')",
            name="valid_metric_type",
        ),
        Index("idx_system_metrics_name", "metric_name"),
        Index("idx_system_metrics_recorded_at", "recorded_at"),
        Index("idx_system_metrics_name_time", "metric_name", "recorded_at"),
    )
