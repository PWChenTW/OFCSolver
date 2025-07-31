-- ClickHouse initialization script for OFC Analytics
-- This script creates the necessary databases and tables for analytics

-- Create analytics database
CREATE DATABASE IF NOT EXISTS ofc_analytics;

-- Use the analytics database
USE ofc_analytics;

-- Game analysis events table
CREATE TABLE IF NOT EXISTS game_events
(
    event_id UUID DEFAULT generateUUIDv4(),
    game_id UUID,
    event_type String,
    player_id UInt8,
    round_number UInt8,
    card_placed String,
    position String,
    timestamp DateTime DEFAULT now(),
    event_data String,
    
    -- Date partition for efficient queries
    event_date Date DEFAULT toDate(timestamp),
    
    -- Indexes
    INDEX idx_game_id game_id TYPE bloom_filter GRANULARITY 4,
    INDEX idx_event_type event_type TYPE set(100) GRANULARITY 2,
    INDEX idx_player_id player_id TYPE minmax GRANULARITY 2
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, game_id, timestamp)
TTL event_date + INTERVAL 90 DAY;

-- Strategy calculation metrics
CREATE TABLE IF NOT EXISTS calculation_metrics
(
    metric_id UUID DEFAULT generateUUIDv4(),
    position_hash String,
    calculation_method Enum('heuristic' = 1, 'monte_carlo' = 2, 'exhaustive' = 3, 'hybrid' = 4),
    calculation_time_ms UInt32,
    tree_nodes_explored UInt64,
    memory_used_mb UInt32,
    cpu_cores_used UInt8,
    confidence_level Float32,
    timestamp DateTime DEFAULT now(),
    
    -- Additional metrics
    cache_hit Bool DEFAULT false,
    pruning_effectiveness Float32,
    
    -- Date partition
    metric_date Date DEFAULT toDate(timestamp),
    
    -- Indexes
    INDEX idx_position_hash position_hash TYPE bloom_filter GRANULARITY 4,
    INDEX idx_method calculation_method TYPE minmax GRANULARITY 1
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(metric_date)
ORDER BY (metric_date, calculation_method, timestamp)
TTL metric_date + INTERVAL 30 DAY;

-- Player performance analytics
CREATE TABLE IF NOT EXISTS player_performance
(
    performance_id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    user_id Nullable(UUID),
    scenario_id String,
    decision_time_seconds UInt16,
    is_correct Bool,
    ev_difference Float32,
    difficulty_level Enum('beginner' = 1, 'intermediate' = 2, 'advanced' = 3, 'expert' = 4),
    timestamp DateTime DEFAULT now(),
    
    -- Aggregated metrics
    running_accuracy Float32,
    improvement_rate Float32,
    
    -- Date partition
    performance_date Date DEFAULT toDate(timestamp),
    
    -- Indexes
    INDEX idx_session_id session_id TYPE bloom_filter GRANULARITY 4,
    INDEX idx_user_id user_id TYPE bloom_filter GRANULARITY 4,
    INDEX idx_difficulty difficulty_level TYPE minmax GRANULARITY 1
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(performance_date)
ORDER BY (performance_date, session_id, timestamp);

-- API request analytics
CREATE TABLE IF NOT EXISTS api_requests
(
    request_id UUID DEFAULT generateUUIDv4(),
    endpoint String,
    method Enum('GET' = 1, 'POST' = 2, 'PUT' = 3, 'DELETE' = 4),
    status_code UInt16,
    response_time_ms UInt32,
    user_agent String,
    ip_address IPv4,
    timestamp DateTime DEFAULT now(),
    
    -- Request details
    request_size_bytes UInt32,
    response_size_bytes UInt32,
    error_message Nullable(String),
    
    -- Date partition
    request_date Date DEFAULT toDate(timestamp),
    
    -- Indexes
    INDEX idx_endpoint endpoint TYPE bloom_filter GRANULARITY 4,
    INDEX idx_status_code status_code TYPE minmax GRANULARITY 2
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(request_date)
ORDER BY (request_date, endpoint, timestamp)
TTL request_date + INTERVAL 60 DAY;

-- Aggregated game statistics (materialized view)
CREATE MATERIALIZED VIEW IF NOT EXISTS game_stats_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour_date)
ORDER BY (hour_date, hour, rules_variant)
AS SELECT
    toDate(timestamp) as hour_date,
    toStartOfHour(timestamp) as hour,
    event_data.rules_variant as rules_variant,
    count() as total_games,
    countIf(event_type = 'game_completed') as completed_games,
    countIf(event_type = 'game_abandoned') as abandoned_games,
    avg(event_data.duration_minutes) as avg_game_duration
FROM game_events
WHERE event_type IN ('game_started', 'game_completed', 'game_abandoned')
GROUP BY hour_date, hour, rules_variant;

-- Solver performance statistics (materialized view)
CREATE MATERIALIZED VIEW IF NOT EXISTS solver_stats_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day_date)
ORDER BY (day_date, calculation_method)
AS SELECT
    toDate(timestamp) as day_date,
    calculation_method,
    count() as total_calculations,
    avg(calculation_time_ms) as avg_calculation_time,
    quantile(0.5)(calculation_time_ms) as median_calculation_time,
    quantile(0.95)(calculation_time_ms) as p95_calculation_time,
    avg(confidence_level) as avg_confidence,
    sum(tree_nodes_explored) as total_nodes_explored,
    avg(memory_used_mb) as avg_memory_used,
    countIf(cache_hit) as cache_hits
FROM calculation_metrics
GROUP BY day_date, calculation_method;

-- Training progress statistics (materialized view)
CREATE MATERIALIZED VIEW IF NOT EXISTS training_stats_weekly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(week_date)
ORDER BY (week_date, difficulty_level)
AS SELECT
    toMonday(timestamp) as week_date,
    difficulty_level,
    count() as total_scenarios,
    countIf(is_correct) as correct_answers,
    avg(decision_time_seconds) as avg_decision_time,
    avg(ev_difference) as avg_ev_difference,
    avg(running_accuracy) as avg_accuracy,
    avg(improvement_rate) as avg_improvement
FROM player_performance
GROUP BY week_date, difficulty_level;

-- API performance statistics (materialized view)
CREATE MATERIALIZED VIEW IF NOT EXISTS api_stats_minute
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(minute_date)
ORDER BY (minute_date, minute, endpoint)
AS SELECT
    toDate(timestamp) as minute_date,
    toStartOfMinute(timestamp) as minute,
    endpoint,
    count() as request_count,
    avg(response_time_ms) as avg_response_time,
    quantile(0.5)(response_time_ms) as median_response_time,
    quantile(0.99)(response_time_ms) as p99_response_time,
    countIf(status_code >= 400) as error_count,
    sum(request_size_bytes) as total_request_bytes,
    sum(response_size_bytes) as total_response_bytes
FROM api_requests
GROUP BY minute_date, minute, endpoint;

-- Create sample data for testing (optional, remove in production)
-- INSERT INTO game_events (game_id, event_type, player_id, round_number, event_data) 
-- VALUES 
--     (generateUUIDv4(), 'game_started', 0, 1, '{"rules_variant": "standard", "player_count": 2}'),
--     (generateUUIDv4(), 'card_placed', 1, 1, '{"card": "AS", "position": "bottom_1"}');

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT ON ofc_analytics.* TO 'analytics_user';

-- Create TTL policy for old data cleanup
ALTER TABLE game_events MODIFY TTL event_date + INTERVAL 90 DAY;
ALTER TABLE calculation_metrics MODIFY TTL metric_date + INTERVAL 30 DAY;
ALTER TABLE api_requests MODIFY TTL request_date + INTERVAL 60 DAY;

-- Optimization: Create projections for common queries
ALTER TABLE game_events ADD PROJECTION game_events_by_player
(
    SELECT *
    ORDER BY player_id, game_id, timestamp
);

ALTER TABLE calculation_metrics ADD PROJECTION metrics_by_position
(
    SELECT *
    ORDER BY position_hash, timestamp
);

-- Create dictionary for fast lookups (example)
CREATE DICTIONARY IF NOT EXISTS scenario_lookup
(
    scenario_id String,
    scenario_name String,
    difficulty_level String,
    optimal_strategy String
)
PRIMARY KEY scenario_id
SOURCE(FILE(path '/var/lib/clickhouse/user_files/scenarios.csv' format 'CSV'))
LIFETIME(MIN 300 MAX 3600)
LAYOUT(FLAT());

SELECT 'ClickHouse initialization completed successfully' as status;