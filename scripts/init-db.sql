-- Initial database setup for OFC Solver System
-- This script runs during Docker container initialization

-- Create application database if it doesn't exist
SELECT 'CREATE DATABASE ofc_solver'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ofc_solver');

-- Create test database if it doesn't exist
SELECT 'CREATE DATABASE ofc_solver_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ofc_solver_test');

-- Connect to the main database
\c ofc_solver;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create application user with appropriate permissions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ofc_app') THEN
        CREATE ROLE ofc_app LOGIN PASSWORD 'ofc_app_password';
    END IF;
END
$$;

-- Grant permissions
GRANT CONNECT ON DATABASE ofc_solver TO ofc_app;
GRANT USAGE ON SCHEMA public TO ofc_app;
GRANT CREATE ON SCHEMA public TO ofc_app;

-- Create basic tables structure (will be managed by Alembic later)

-- Games table
CREATE TABLE IF NOT EXISTS games (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_count INTEGER NOT NULL CHECK (player_count BETWEEN 2 AND 4),
    rules_variant VARCHAR(50) NOT NULL DEFAULT 'standard',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    final_scores JSONB,
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'completed', 'paused', 'cancelled'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_games_created_at ON games(created_at);
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);
CREATE INDEX IF NOT EXISTS idx_games_completed_at ON games(completed_at) WHERE completed_at IS NOT NULL;

-- Positions table for game states
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL CHECK (round_number > 0),
    current_player INTEGER NOT NULL CHECK (current_player >= 0),
    players_hands JSONB NOT NULL,
    remaining_cards INTEGER[] NOT NULL,
    position_hash VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(game_id, round_number, current_player)
);

-- Create indexes for positions
CREATE INDEX IF NOT EXISTS idx_positions_game_id ON positions(game_id);
CREATE INDEX IF NOT EXISTS idx_positions_hash ON positions(position_hash);
CREATE INDEX IF NOT EXISTS idx_positions_created_at ON positions(created_at);

-- Analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id UUID REFERENCES positions(id) ON DELETE CASCADE,
    optimal_strategy JSONB NOT NULL,
    expected_value DECIMAL(10,6) NOT NULL,
    calculation_method VARCHAR(20) NOT NULL,
    calculation_time_ms INTEGER NOT NULL CHECK (calculation_time_ms >= 0),
    confidence_level DECIMAL(4,3) CHECK (confidence_level BETWEEN 0 AND 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_calculation_method CHECK (
        calculation_method IN ('heuristic', 'monte_carlo', 'exhaustive', 'hybrid')
    )
);

-- Create indexes for analysis results
CREATE INDEX IF NOT EXISTS idx_analysis_position_id ON analysis_results(position_id);
CREATE INDEX IF NOT EXISTS idx_analysis_method ON analysis_results(calculation_method);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_results(created_at);

-- Training sessions table
CREATE TABLE IF NOT EXISTS training_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- NULL for anonymous sessions
    difficulty_level VARCHAR(20) NOT NULL DEFAULT 'intermediate',
    scenario_type VARCHAR(30) NOT NULL DEFAULT 'general',
    total_scenarios INTEGER NOT NULL CHECK (total_scenarios > 0),
    completed_scenarios INTEGER NOT NULL DEFAULT 0 CHECK (completed_scenarios >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_difficulty CHECK (
        difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')
    ),
    CONSTRAINT valid_session_status CHECK (
        status IN ('active', 'completed', 'paused', 'abandoned')
    ),
    CONSTRAINT completed_not_exceed_total CHECK (completed_scenarios <= total_scenarios)
);

-- Create indexes for training sessions
CREATE INDEX IF NOT EXISTS idx_training_user_id ON training_sessions(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_training_status ON training_sessions(status);
CREATE INDEX IF NOT EXISTS idx_training_started_at ON training_sessions(started_at);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES training_sessions(id) ON DELETE CASCADE,
    scenario_id VARCHAR(100) NOT NULL,
    user_answer VARCHAR(200),
    optimal_answer VARCHAR(200) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    ev_difference DECIMAL(8,4),
    decision_time_seconds INTEGER NOT NULL CHECK (decision_time_seconds >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance metrics
CREATE INDEX IF NOT EXISTS idx_performance_session_id ON performance_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_performance_created_at ON performance_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_performance_is_correct ON performance_metrics(is_correct);

-- System metrics table for monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_type VARCHAR(20) NOT NULL DEFAULT 'gauge',
    tags JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_metric_type CHECK (
        metric_type IN ('counter', 'gauge', 'histogram', 'summary')
    )
);

-- Create indexes for system metrics
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time ON system_metrics(metric_name, recorded_at);

-- Grant permissions on tables to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ofc_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ofc_app;

-- Create a simple health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TABLE(status TEXT, check_time TIMESTAMP WITH TIME ZONE) AS $$
BEGIN
    RETURN QUERY SELECT 'healthy'::TEXT, NOW();
END;
$$ LANGUAGE plpgsql;

-- Setup complete
SELECT 'Database initialization completed successfully' as status;