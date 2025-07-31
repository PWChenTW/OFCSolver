"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-07-31

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create games table
    op.create_table(
        "games",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_count", sa.Integer(), nullable=False),
        sa.Column("rules_variant", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_scores", sa.JSON(), nullable=True),
        sa.CheckConstraint("player_count BETWEEN 2 AND 4", name="valid_player_count"),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'paused', 'cancelled')",
            name="valid_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_games"),
    )
    op.create_index("idx_games_completed_at", "games", ["completed_at"], unique=False)
    op.create_index("idx_games_created_at", "games", ["created_at"], unique=False)
    op.create_index("idx_games_status", "games", ["status"], unique=False)

    # Create positions table
    op.create_table(
        "positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("current_player", sa.Integer(), nullable=False),
        sa.Column("players_hands", sa.JSON(), nullable=False),
        sa.Column("remaining_cards", sa.JSON(), nullable=False),
        sa.Column("position_hash", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint("current_player >= 0", name="valid_current_player"),
        sa.CheckConstraint("round_number > 0", name="valid_round_number"),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            name="fk_positions_game_id_games",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_positions"),
    )
    op.create_index(
        "idx_positions_created_at", "positions", ["created_at"], unique=False
    )
    op.create_index("idx_positions_game_id", "positions", ["game_id"], unique=False)
    op.create_index(
        "idx_positions_game_round_player",
        "positions",
        ["game_id", "round_number", "current_player"],
        unique=True,
    )
    op.create_index("idx_positions_hash", "positions", ["position_hash"], unique=False)

    # Create analysis_results table
    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("optimal_strategy", sa.JSON(), nullable=False),
        sa.Column("expected_value", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("calculation_method", sa.String(length=20), nullable=False),
        sa.Column("calculation_time_ms", sa.Integer(), nullable=False),
        sa.Column("confidence_level", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "calculation_method IN ('heuristic', 'monte_carlo', 'exhaustive', 'hybrid')",
            name="valid_calculation_method",
        ),
        sa.CheckConstraint("calculation_time_ms >= 0", name="valid_calculation_time"),
        sa.CheckConstraint(
            "confidence_level BETWEEN 0 AND 1", name="valid_confidence_level"
        ),
        sa.ForeignKeyConstraint(
            ["position_id"],
            ["positions.id"],
            name="fk_analysis_results_position_id_positions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_analysis_results"),
    )
    op.create_index(
        "idx_analysis_created_at", "analysis_results", ["created_at"], unique=False
    )
    op.create_index(
        "idx_analysis_method", "analysis_results", ["calculation_method"], unique=False
    )
    op.create_index(
        "idx_analysis_position_id", "analysis_results", ["position_id"], unique=False
    )

    # Create training_sessions table
    op.create_table(
        "training_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("difficulty_level", sa.String(length=20), nullable=False),
        sa.Column("scenario_type", sa.String(length=30), nullable=False),
        sa.Column("total_scenarios", sa.Integer(), nullable=False),
        sa.Column("completed_scenarios", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "completed_scenarios <= total_scenarios", name="completed_not_exceed_total"
        ),
        sa.CheckConstraint(
            "completed_scenarios >= 0", name="valid_completed_scenarios"
        ),
        sa.CheckConstraint(
            "difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')",
            name="valid_difficulty",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'paused', 'abandoned')",
            name="valid_session_status",
        ),
        sa.CheckConstraint("total_scenarios > 0", name="valid_total_scenarios"),
        sa.PrimaryKeyConstraint("id", name="pk_training_sessions"),
    )
    op.create_index(
        "idx_training_started_at", "training_sessions", ["started_at"], unique=False
    )
    op.create_index(
        "idx_training_status", "training_sessions", ["status"], unique=False
    )
    op.create_index(
        "idx_training_user_id", "training_sessions", ["user_id"], unique=False
    )

    # Create performance_metrics table
    op.create_table(
        "performance_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_id", sa.String(length=100), nullable=False),
        sa.Column("user_answer", sa.String(length=200), nullable=True),
        sa.Column("optimal_answer", sa.String(length=200), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("ev_difference", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("decision_time_seconds", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint("decision_time_seconds >= 0", name="valid_decision_time"),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["training_sessions.id"],
            name="fk_performance_metrics_session_id_training_sessions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_performance_metrics"),
    )
    op.create_index(
        "idx_performance_created_at",
        "performance_metrics",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "idx_performance_is_correct",
        "performance_metrics",
        ["is_correct"],
        unique=False,
    )
    op.create_index(
        "idx_performance_session_id",
        "performance_metrics",
        ["session_id"],
        unique=False,
    )

    # Create system_metrics table
    op.create_table(
        "system_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column("metric_type", sa.String(length=20), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "metric_type IN ('counter', 'gauge', 'histogram', 'summary')",
            name="valid_metric_type",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_system_metrics"),
    )
    op.create_index(
        "idx_system_metrics_name", "system_metrics", ["metric_name"], unique=False
    )
    op.create_index(
        "idx_system_metrics_name_time",
        "system_metrics",
        ["metric_name", "recorded_at"],
        unique=False,
    )
    op.create_index(
        "idx_system_metrics_recorded_at",
        "system_metrics",
        ["recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_system_metrics_recorded_at", table_name="system_metrics")
    op.drop_index("idx_system_metrics_name_time", table_name="system_metrics")
    op.drop_index("idx_system_metrics_name", table_name="system_metrics")
    op.drop_table("system_metrics")

    op.drop_index("idx_performance_session_id", table_name="performance_metrics")
    op.drop_index("idx_performance_is_correct", table_name="performance_metrics")
    op.drop_index("idx_performance_created_at", table_name="performance_metrics")
    op.drop_table("performance_metrics")

    op.drop_index("idx_training_user_id", table_name="training_sessions")
    op.drop_index("idx_training_status", table_name="training_sessions")
    op.drop_index("idx_training_started_at", table_name="training_sessions")
    op.drop_table("training_sessions")

    op.drop_index("idx_analysis_position_id", table_name="analysis_results")
    op.drop_index("idx_analysis_method", table_name="analysis_results")
    op.drop_index("idx_analysis_created_at", table_name="analysis_results")
    op.drop_table("analysis_results")

    op.drop_index("idx_positions_hash", table_name="positions")
    op.drop_index("idx_positions_game_round_player", table_name="positions")
    op.drop_index("idx_positions_game_id", table_name="positions")
    op.drop_index("idx_positions_created_at", table_name="positions")
    op.drop_table("positions")

    op.drop_index("idx_games_status", table_name="games")
    op.drop_index("idx_games_created_at", table_name="games")
    op.drop_index("idx_games_completed_at", table_name="games")
    op.drop_table("games")
