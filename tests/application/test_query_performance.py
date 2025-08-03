"""Performance tests for query handlers."""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock

from src.application.queries import PaginationParams, TimeRange
from src.application.queries.game_queries import (
    GetActiveGamesQuery, GetActiveGamesHandler,
    GetGameHistoryQuery, GetGameHistoryHandler,
    GetGameStatsQuery, GetGameStatsHandler
)
from src.application.queries.analysis_queries import (
    GetAnalysisHistoryQuery, GetAnalysisHistoryHandler,
    CompareAnalysisResultsQuery, CompareAnalysisResultsHandler
)
from src.application.queries.training_queries import (
    GetTrainingHistoryQuery, GetTrainingHistoryHandler,
    GetLeaderboardQuery, GetLeaderboardHandler,
    LeaderboardType
)
from src.application.queries.query_optimization import (
    QueryOptimizer, CacheConfig, QueryOptimizationMiddleware
)
from src.domain.entities.game import Game, GameStatus
from src.domain.entities.player import Player
from src.domain.entities.strategy import AnalysisSession, CalculationStatus
from src.domain.entities.training import TrainingSession
from src.domain.value_objects.difficulty import Difficulty, DifficultyLevel


class PerformanceMetrics:
    """Helper class to collect performance metrics."""
    
    def __init__(self):
        self.execution_times = []
        self.memory_usage = []
        self.query_counts = 0
    
    def record_execution(self, execution_time: float, memory_used: int = 0):
        self.execution_times.append(execution_time)
        self.memory_usage.append(memory_used)
        self.query_counts += 1
    
    def get_summary(self) -> Dict[str, Any]:
        if not self.execution_times:
            return {}
        
        sorted_times = sorted(self.execution_times)
        return {
            'total_queries': self.query_counts,
            'avg_time': sum(self.execution_times) / len(self.execution_times),
            'min_time': min(self.execution_times),
            'max_time': max(self.execution_times),
            'p50_time': sorted_times[len(sorted_times) // 2],
            'p95_time': sorted_times[int(len(sorted_times) * 0.95)],
            'p99_time': sorted_times[int(len(sorted_times) * 0.99)],
            'total_memory': sum(self.memory_usage)
        }


@pytest.fixture
def mock_repositories():
    """Create mock repositories for testing."""
    return {
        'game_repository': AsyncMock(),
        'player_repository': AsyncMock(),
        'analysis_repository': AsyncMock(),
        'strategy_repository': AsyncMock(),
        'calculation_repository': AsyncMock(),
        'training_repository': AsyncMock(),
        'scenario_repository': AsyncMock()
    }


@pytest.fixture
def query_optimizer():
    """Create query optimizer for testing."""
    cache_manager = AsyncMock()
    health_checker = AsyncMock()
    return QueryOptimizer(cache_manager, health_checker)


def create_mock_games(count: int) -> List[Game]:
    """Create mock game entities."""
    games = []
    for i in range(count):
        game = MagicMock(spec=Game)
        game.id = uuid.uuid4()
        game.status = GameStatus.IN_PROGRESS if i % 2 == 0 else GameStatus.COMPLETED
        game.created_at = datetime.now() - timedelta(days=i)
        game.updated_at = datetime.now() - timedelta(hours=i)
        game.completed_at = None if game.status == GameStatus.IN_PROGRESS else game.updated_at
        game.current_round = i % 10 + 1
        game.current_player_id = uuid.uuid4() if game.status == GameStatus.IN_PROGRESS else None
        
        # Mock players
        game.players = []
        for j in range(2):
            player = MagicMock(spec=Player)
            player.id = uuid.uuid4()
            player.position = MagicMock()
            player.position.value = j
            player.score = i * 10 + j
            player.is_active = True
            player.in_fantasy_land = False
            game.players.append(player)
        
        games.append(game)
    
    return games


def create_mock_sessions(count: int) -> List[AnalysisSession]:
    """Create mock analysis sessions."""
    sessions = []
    for i in range(count):
        session = MagicMock(spec=AnalysisSession)
        session.id = uuid.uuid4()
        session.game_id = uuid.uuid4()
        session.user_id = uuid.uuid4()
        session.status = CalculationStatus.COMPLETED if i % 3 == 0 else CalculationStatus.IN_PROGRESS
        session.created_at = datetime.now() - timedelta(days=i)
        session.started_at = session.created_at + timedelta(minutes=1)
        session.completed_at = session.started_at + timedelta(minutes=i * 2) if session.status == CalculationStatus.COMPLETED else None
        session.progress = 1.0 if session.status == CalculationStatus.COMPLETED else 0.5
        session.parameters = {'type': 'position', 'depth': i % 5 + 1}
        sessions.append(session)
    
    return sessions


def create_mock_training_sessions(count: int) -> List[TrainingSession]:
    """Create mock training sessions."""
    sessions = []
    for i in range(count):
        session = MagicMock(spec=TrainingSession)
        session.id = uuid.uuid4()
        session.user_id = uuid.uuid4()
        session.scenario_id = uuid.uuid4()
        session.difficulty = MagicMock(spec=Difficulty)
        session.difficulty.level = DifficultyLevel.MEDIUM
        session.started_at = datetime.now() - timedelta(days=i)
        session.completed_at = session.started_at + timedelta(minutes=30) if i % 2 == 0 else None
        session.is_completed = i % 2 == 0
        session.score = 80 + (i % 20)
        session.exercises = []
        session.get_average_accuracy = Mock(return_value=0.75 + (i % 10) / 100)
        session.get_duration = Mock(return_value=1800)  # 30 minutes
        sessions.append(session)
    
    return sessions


@pytest.mark.asyncio
class TestGameQueryPerformance:
    """Performance tests for game queries."""
    
    async def test_get_active_games_performance(self, mock_repositories):
        """Test performance of getting active games."""
        game_repo = mock_repositories['game_repository']
        handler = GetActiveGamesHandler(game_repo)
        metrics = PerformanceMetrics()
        
        # Setup mock data
        mock_games = create_mock_games(1000)
        game_repo.find_active.return_value = mock_games[:20]
        game_repo.count_active.return_value = 500
        
        # Test various page sizes
        page_sizes = [10, 20, 50, 100]
        
        for page_size in page_sizes:
            for page in range(1, 11):  # Test 10 pages
                query = GetActiveGamesQuery(
                    pagination=PaginationParams(page=page, page_size=page_size)
                )
                
                start_time = time.time()
                result = await handler.handle(query)
                execution_time = time.time() - start_time
                
                metrics.record_execution(execution_time)
                
                assert len(result.games.items) <= page_size
                assert result.games.total == 500
        
        summary = metrics.get_summary()
        print(f"\nGetActiveGames Performance: {summary}")
        
        # Performance assertions
        assert summary['avg_time'] < 0.01  # Average should be under 10ms
        assert summary['p95_time'] < 0.02  # 95th percentile under 20ms
    
    async def test_get_game_history_with_filters_performance(self, mock_repositories):
        """Test performance of game history queries with various filters."""
        game_repo = mock_repositories['game_repository']
        handler = GetGameHistoryHandler(game_repo)
        metrics = PerformanceMetrics()
        
        # Setup mock data
        mock_games = create_mock_games(5000)
        game_repo.find_by_criteria.return_value = mock_games[:50]
        game_repo.count_by_criteria.return_value = 2500
        
        # Test different filter combinations
        test_cases = [
            # Simple queries
            {'player_id': uuid.uuid4()},
            {'status_filter': [GameStatus.COMPLETED]},
            
            # Complex queries
            {
                'player_id': uuid.uuid4(),
                'status_filter': [GameStatus.COMPLETED, GameStatus.IN_PROGRESS],
                'date_filter': {'start_date': datetime.now() - timedelta(days=30)}
            },
            
            # Heavy queries
            {
                'status_filter': [GameStatus.COMPLETED],
                'date_filter': {
                    'start_date': datetime.now() - timedelta(days=365),
                    'end_date': datetime.now()
                }
            }
        ]
        
        for filters in test_cases:
            for _ in range(10):  # Run each query 10 times
                query = GetGameHistoryQuery(
                    pagination=PaginationParams(page=1, page_size=50),
                    **filters
                )
                
                start_time = time.time()
                result = await handler.handle(query)
                execution_time = time.time() - start_time
                
                metrics.record_execution(execution_time)
        
        summary = metrics.get_summary()
        print(f"\nGetGameHistory Performance: {summary}")
        
        # Performance assertions
        assert summary['avg_time'] < 0.015  # Average under 15ms
        assert summary['p99_time'] < 0.03   # 99th percentile under 30ms


@pytest.mark.asyncio
class TestAnalysisQueryPerformance:
    """Performance tests for analysis queries."""
    
    async def test_analysis_history_pagination_performance(self, mock_repositories):
        """Test performance of paginated analysis history queries."""
        analysis_repo = mock_repositories['analysis_repository']
        handler = GetAnalysisHistoryHandler(analysis_repo)
        metrics = PerformanceMetrics()
        
        # Setup mock data
        mock_sessions = create_mock_sessions(10000)
        
        # Test large offset pagination
        test_cases = [
            (1, 20),      # First page
            (50, 20),     # Mid-range page
            (100, 20),    # Deep pagination
            (500, 20),    # Very deep pagination
            (1, 100),     # Large page size
            (10, 100),    # Large page with offset
        ]
        
        for page, page_size in test_cases:
            analysis_repo.find_by_criteria.return_value = mock_sessions[:page_size]
            analysis_repo.count_by_criteria.return_value = 10000
            
            query = GetAnalysisHistoryQuery(
                pagination=PaginationParams(page=page, page_size=page_size)
            )
            
            start_time = time.time()
            result = await handler.handle(query)
            execution_time = time.time() - start_time
            
            metrics.record_execution(execution_time)
            
            # Verify results
            assert len(result.sessions.items) <= page_size
            assert result.sessions.total == 10000
        
        summary = metrics.get_summary()
        print(f"\nAnalysisHistory Pagination Performance: {summary}")
        
        # Performance should not degrade significantly with deep pagination
        assert summary['max_time'] < summary['avg_time'] * 3
    
    async def test_compare_analysis_results_performance(self, mock_repositories):
        """Test performance of comparing multiple analysis results."""
        analysis_repo = mock_repositories['analysis_repository']
        calc_repo = mock_repositories['calculation_repository']
        handler = CompareAnalysisResultsHandler(analysis_repo, calc_repo)
        metrics = PerformanceMetrics()
        
        # Setup mock data
        mock_sessions = create_mock_sessions(20)
        for session in mock_sessions:
            analysis_repo.get_by_id.return_value = session
        
        mock_calculation = MagicMock()
        mock_calculation.ev_results = {'total': 100.0}
        mock_calculation.confidence_intervals = {'total': (90.0, 110.0)}
        mock_calculation.calculation_time = 5.0
        mock_calculation.iterations = 10000
        calc_repo.find_by_session.return_value = [mock_calculation]
        
        # Test comparing different numbers of sessions
        session_counts = [2, 5, 10, 20]
        
        for count in session_counts:
            session_ids = [uuid.uuid4() for _ in range(count)]
            
            query = CompareAnalysisResultsQuery(
                session_ids=session_ids,
                comparison_metrics=['expected_value', 'confidence', 'calculation_time']
            )
            
            start_time = time.time()
            result = await handler.handle(query)
            execution_time = time.time() - start_time
            
            metrics.record_execution(execution_time)
            
            # Verify results
            assert len(result.comparison.session_ids) == count
            assert 'expected_value' in result.comparison.metrics
        
        summary = metrics.get_summary()
        print(f"\nCompareAnalysis Performance: {summary}")
        
        # Performance should scale linearly with session count
        assert summary['avg_time'] < 0.05  # Average under 50ms


@pytest.mark.asyncio
class TestTrainingQueryPerformance:
    """Performance tests for training queries."""
    
    async def test_training_history_performance(self, mock_repositories):
        """Test performance of training history queries."""
        training_repo = mock_repositories['training_repository']
        handler = GetTrainingHistoryHandler(training_repo)
        metrics = PerformanceMetrics()
        
        # Setup mock data
        mock_sessions = create_mock_training_sessions(5000)
        
        # Test with various filters
        test_scenarios = [
            # Basic query
            {'completed_only': False},
            
            # Filtered query
            {
                'scenario_id': uuid.uuid4(),
                'difficulty_filter': [DifficultyLevel.EASY, DifficultyLevel.MEDIUM],
                'completed_only': True
            },
            
            # Date range query
            {
                'date_filter': {
                    'start_date': datetime.now() - timedelta(days=30),
                    'end_date': datetime.now()
                }
            }
        ]
        
        for filters in test_scenarios:
            training_repo.find_by_criteria.return_value = mock_sessions[:50]
            training_repo.count_by_criteria.return_value = 2500
            
            query = GetTrainingHistoryQuery(
                user_id=uuid.uuid4(),
                pagination=PaginationParams(page=1, page_size=50),
                **filters
            )
            
            start_time = time.time()
            result = await handler.handle(query)
            execution_time = time.time() - start_time
            
            metrics.record_execution(execution_time)
        
        summary = metrics.get_summary()
        print(f"\nTrainingHistory Performance: {summary}")
        
        # Performance assertions
        assert summary['avg_time'] < 0.02  # Average under 20ms
    
    async def test_leaderboard_performance(self, mock_repositories):
        """Test performance of leaderboard queries."""
        training_repo = mock_repositories['training_repository']
        handler = GetLeaderboardHandler(training_repo)
        metrics = PerformanceMetrics()
        
        # Mock leaderboard data
        mock_entries = []
        for i in range(1000):
            mock_entries.append({
                'user_id': uuid.uuid4(),
                'username': f'user_{i}',
                'score': 1000 - i,
                'accuracy': 0.9 - (i * 0.0001),
                'sessions_completed': 100 - (i % 50),
                'total_time': 3600 * (i + 1),
                'best_performance': {'score': 1000 - i}
            })
        
        # Test different leaderboard types
        leaderboard_types = [
            LeaderboardType.DAILY,
            LeaderboardType.WEEKLY,
            LeaderboardType.MONTHLY,
            LeaderboardType.ALL_TIME
        ]
        
        for lb_type in leaderboard_types:
            # Mock the handler's internal method
            handler._get_leaderboard_data = AsyncMock(
                return_value=(mock_entries[:100], 1000, lb_type.value)
            )
            
            query = GetLeaderboardQuery(
                leaderboard_type=lb_type,
                time_range=TimeRange.LAST_WEEK,
                pagination=PaginationParams(page=1, page_size=100)
            )
            
            start_time = time.time()
            result = await handler.handle(query)
            execution_time = time.time() - start_time
            
            metrics.record_execution(execution_time)
            
            # Verify results
            assert len(result.entries.items) == 100
            assert result.entries.total == 1000
        
        summary = metrics.get_summary()
        print(f"\nLeaderboard Performance: {summary}")
        
        # Leaderboard queries should be fast
        assert summary['avg_time'] < 0.01  # Average under 10ms
        assert summary['p99_time'] < 0.02  # 99th percentile under 20ms


@pytest.mark.asyncio
class TestQueryOptimizationPerformance:
    """Test query optimization features."""
    
    async def test_cache_performance(self, query_optimizer, mock_repositories):
        """Test performance improvement with caching."""
        game_repo = mock_repositories['game_repository']
        
        # Create handler with caching
        @query_optimizer.cache_query(CacheConfig(ttl_seconds=60))
        async def cached_handler(self, query):
            return await GetActiveGamesHandler(game_repo).handle(query)
        
        # Setup mock data
        mock_games = create_mock_games(100)
        game_repo.find_active.return_value = mock_games[:20]
        game_repo.count_active.return_value = 100
        
        # Create a handler instance
        handler = MagicMock()
        
        # First call - cache miss
        query = GetActiveGamesQuery(pagination=PaginationParams(page=1, page_size=20))
        
        start_time = time.time()
        result1 = await cached_handler(handler, query)
        first_call_time = time.time() - start_time
        
        # Second call - cache hit
        start_time = time.time()
        result2 = await cached_handler(handler, query)
        second_call_time = time.time() - start_time
        
        print(f"\nCache Performance:")
        print(f"  First call (miss): {first_call_time:.4f}s")
        print(f"  Second call (hit): {second_call_time:.4f}s")
        print(f"  Speedup: {first_call_time / second_call_time:.1f}x")
        
        # Cache hit should be significantly faster
        assert second_call_time < first_call_time * 0.1
        
        # Results should be identical
        assert result1.games.total == result2.games.total
    
    async def test_batch_query_performance(self, query_optimizer, mock_repositories):
        """Test performance improvement with query batching."""
        game_repo = mock_repositories['game_repository']
        
        # Create batched handler
        @query_optimizer.batch_queries(batch_size=5, delay_ms=10)
        async def batched_handler(self, queries):
            # Simulate batch processing
            results = []
            for query in queries:
                result = await GetActiveGamesHandler(game_repo).handle(query)
                results.append(result)
            return results
        
        # Setup mock data
        mock_games = create_mock_games(100)
        game_repo.find_active.return_value = mock_games[:20]
        game_repo.count_active.return_value = 100
        
        handler = MagicMock()
        
        # Create multiple concurrent queries
        queries = [
            GetActiveGamesQuery(pagination=PaginationParams(page=i, page_size=20))
            for i in range(1, 11)
        ]
        
        # Execute queries concurrently
        start_time = time.time()
        tasks = [batched_handler(handler, query) for query in queries]
        results = await asyncio.gather(*tasks)
        batch_time = time.time() - start_time
        
        # Compare with sequential execution
        start_time = time.time()
        sequential_results = []
        for query in queries:
            result = await GetActiveGamesHandler(game_repo).handle(query)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        print(f"\nBatch Query Performance:")
        print(f"  Batch execution: {batch_time:.4f}s")
        print(f"  Sequential execution: {sequential_time:.4f}s")
        print(f"  Speedup: {sequential_time / batch_time:.1f}x")
        
        # Batch should be faster than sequential
        assert batch_time < sequential_time
    
    async def test_query_stats_collection(self, query_optimizer, mock_repositories):
        """Test query statistics collection."""
        game_repo = mock_repositories['game_repository']
        handler = GetActiveGamesHandler(game_repo)
        
        # Setup mock data
        mock_games = create_mock_games(100)
        game_repo.find_active.return_value = mock_games[:20]
        game_repo.count_active.return_value = 100
        
        # Execute multiple queries with varying response times
        for i in range(100):
            query = GetActiveGamesQuery(
                pagination=PaginationParams(page=i % 10 + 1, page_size=20)
            )
            
            # Simulate varying response times
            if i % 10 == 0:
                await asyncio.sleep(0.05)  # Simulate slow query
            
            await handler.handle(query)
        
        # Get statistics
        stats = query_optimizer.get_query_stats('GetActiveGamesHandler')
        
        print(f"\nQuery Statistics: {stats}")
        
        # Verify statistics were collected
        assert stats.get('count', 0) > 0
        assert 'avg_execution_time' in stats
        assert 'p95_execution_time' in stats


@pytest.mark.asyncio
class TestQueryOptimizationMiddleware:
    """Test query optimization middleware."""
    
    async def test_middleware_auto_optimization(self, query_optimizer, mock_repositories):
        """Test automatic query optimization based on query type."""
        game_repo = mock_repositories['game_repository']
        middleware = QueryOptimizationMiddleware(query_optimizer)
        
        # Setup mock data
        mock_games = create_mock_games(100)
        game_repo.find_active.return_value = mock_games[:20]
        game_repo.count_active.return_value = 100
        
        # Test that read queries are automatically cached
        handler = GetActiveGamesHandler(game_repo)
        query = GetActiveGamesQuery(pagination=PaginationParams(page=1, page_size=20))
        
        # First call
        start_time = time.time()
        result1 = await middleware(handler.handle, query)
        first_time = time.time() - start_time
        
        # Second call (should be cached)
        start_time = time.time()
        result2 = await middleware(handler.handle, query)
        second_time = time.time() - start_time
        
        print(f"\nMiddleware Auto-Optimization:")
        print(f"  First call: {first_time:.4f}s")
        print(f"  Second call: {second_time:.4f}s")
        
        # Second call should be faster due to caching
        assert second_time < first_time


if __name__ == "__main__":
    # Run performance tests
    asyncio.run(pytest.main([__file__, "-v", "-s"]))