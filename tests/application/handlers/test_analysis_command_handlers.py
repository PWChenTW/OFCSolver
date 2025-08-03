"""Integration tests for analysis command handlers."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime

from src.application.commands.analysis_commands import (
    RequestAnalysisCommand,
    CancelAnalysisCommand,
    GetAnalysisStatusCommand,
    BatchAnalysisCommand,
    CompareStrategiesCommand
)
from src.application.handlers.analysis_command_handlers import (
    RequestAnalysisCommandHandler,
    CancelAnalysisCommandHandler,
    GetAnalysisStatusCommandHandler,
    BatchAnalysisCommandHandler,
    CompareStrategiesCommandHandler
)
from src.domain.entities.strategy.analysis_session import AnalysisSession, SessionStatus
from src.domain.entities.game.position import Position
from src.domain.value_objects.strategy import Strategy
from src.domain.value_objects.expected_value import ExpectedValue


class TestRequestAnalysisCommandHandler:
    """Test RequestAnalysisCommand handler."""
    
    @pytest.fixture
    def mock_position(self):
        """Create mock position."""
        position = Mock(spec=Position)
        position.remaining_cards = list(range(30))  # 30 cards remaining
        position.players_hands = {"player1": [], "player2": []}
        position.get_hash = Mock(return_value="position_hash_123")
        return position
    
    @pytest.fixture
    def mock_analysis_repository(self):
        """Create mock analysis repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_position_repository(self):
        """Create mock position repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_strategy_calculator(self):
        """Create mock strategy calculator."""
        calculator = AsyncMock()
        strategy = Mock(spec=Strategy)
        strategy.expected_value = ExpectedValue(10.5)
        strategy.confidence = 0.95
        strategy.calculation_method = "optimal"
        calculator.calculate_optimal_strategy = AsyncMock(return_value=strategy)
        calculator.calculate_heuristic_strategy = AsyncMock(return_value=strategy)
        return calculator
    
    @pytest.fixture
    def mock_monte_carlo_simulator(self):
        """Create mock Monte Carlo simulator."""
        simulator = AsyncMock()
        strategy = Mock(spec=Strategy)
        strategy.expected_value = ExpectedValue(9.8)
        strategy.confidence = 0.85
        strategy.calculation_method = "monte_carlo"
        simulator.simulate_position = AsyncMock(return_value=strategy)
        return simulator
    
    @pytest.fixture
    def mock_cache_manager(self):
        """Create mock cache manager."""
        cache = AsyncMock()
        cache.get_strategy = AsyncMock(return_value=None)
        cache.store_strategy = AsyncMock()
        return cache
    
    @pytest.fixture
    def handler(
        self,
        mock_analysis_repository,
        mock_position_repository,
        mock_strategy_calculator,
        mock_monte_carlo_simulator,
        mock_cache_manager
    ):
        """Create handler instance."""
        return RequestAnalysisCommandHandler(
            analysis_repository=mock_analysis_repository,
            position_repository=mock_position_repository,
            strategy_calculator=mock_strategy_calculator,
            monte_carlo_simulator=mock_monte_carlo_simulator,
            cache_manager=mock_cache_manager
        )
    
    @pytest.mark.asyncio
    async def test_request_analysis_cache_hit(
        self,
        handler,
        mock_position,
        mock_cache_manager
    ):
        """Test analysis request returns cached result."""
        # Arrange
        cached_strategy = Mock(spec=Strategy)
        mock_cache_manager.get_strategy = AsyncMock(return_value=cached_strategy)
        
        command = RequestAnalysisCommand(
            position=mock_position,
            analysis_type="optimal",
            calculation_depth=3,
            force_recalculate=False
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert result.data["strategy"] == cached_strategy
        assert result.data["cache_hit"] is True
        assert result.data["session_id"] is None
    
    @pytest.mark.asyncio
    async def test_request_analysis_new_calculation(
        self,
        handler,
        mock_position,
        mock_analysis_repository
    ):
        """Test analysis request starts new calculation."""
        # Arrange
        command = RequestAnalysisCommand(
            position=mock_position,
            analysis_type="optimal",
            calculation_depth=3,
            force_recalculate=True
        )
        
        # Act
        result = await handler.handle(command)
        
        # Wait a bit for async task to start
        await asyncio.sleep(0.1)
        
        # Assert
        assert result.success is True
        assert result.data["status"] == "processing"
        assert result.data["session_id"] is not None
        assert result.data["estimated_time_seconds"] > 0
        assert mock_analysis_repository.save.called
    
    @pytest.mark.asyncio
    async def test_request_analysis_monte_carlo(
        self,
        handler,
        mock_position,
        mock_monte_carlo_simulator
    ):
        """Test Monte Carlo analysis request."""
        # Arrange
        command = RequestAnalysisCommand(
            position=mock_position,
            analysis_type="monte_carlo",
            calculation_depth=3,
            force_recalculate=True
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert result.data["status"] == "processing"


class TestCancelAnalysisCommandHandler:
    """Test CancelAnalysisCommand handler."""
    
    @pytest.fixture
    def mock_analysis_session(self):
        """Create mock analysis session."""
        session = Mock(spec=AnalysisSession)
        session.id = uuid4()
        session.status = SessionStatus.RUNNING
        session.cancel_calculation = Mock()
        session.add_event = Mock()
        return session
    
    @pytest.fixture
    def mock_analysis_repository(self, mock_analysis_session):
        """Create mock analysis repository."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=mock_analysis_session)
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def handler(self, mock_analysis_repository):
        """Create handler instance."""
        return CancelAnalysisCommandHandler(
            analysis_repository=mock_analysis_repository
        )
    
    @pytest.mark.asyncio
    async def test_cancel_analysis_success(
        self,
        handler,
        mock_analysis_session
    ):
        """Test successful analysis cancellation."""
        # Arrange
        command = CancelAnalysisCommand(
            analysis_session_id=mock_analysis_session.id,
            reason="User requested"
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert result.data["status"] == "cancelled"
        assert mock_analysis_session.cancel_calculation.called
    
    @pytest.mark.asyncio
    async def test_cancel_analysis_not_found(
        self,
        handler,
        mock_analysis_repository
    ):
        """Test cancellation fails when session not found."""
        # Arrange
        mock_analysis_repository.get_by_id = AsyncMock(return_value=None)
        command = CancelAnalysisCommand(
            analysis_session_id=uuid4(),
            reason="User requested"
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is False
        assert "Analysis session not found" in result.error
    
    @pytest.mark.asyncio
    async def test_cancel_analysis_already_completed(
        self,
        handler,
        mock_analysis_session
    ):
        """Test cancellation fails when already completed."""
        # Arrange
        mock_analysis_session.status = SessionStatus.COMPLETED
        command = CancelAnalysisCommand(
            analysis_session_id=mock_analysis_session.id
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is False
        assert "Cannot cancel analysis" in result.error


class TestGetAnalysisStatusCommandHandler:
    """Test GetAnalysisStatusCommand handler."""
    
    @pytest.fixture
    def mock_completed_session(self):
        """Create mock completed analysis session."""
        session = Mock(spec=AnalysisSession)
        session.id = uuid4()
        session.status = SessionStatus.COMPLETED
        session.created_at = datetime.utcnow()
        session.completed_at = datetime.utcnow()
        session.analysis_type = "optimal"
        session.result = Mock(spec=Strategy)
        session.calculation_time_ms = 1500
        return session
    
    @pytest.fixture
    def mock_analysis_repository(self, mock_completed_session):
        """Create mock analysis repository."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=mock_completed_session)
        return repo
    
    @pytest.fixture
    def handler(self, mock_analysis_repository):
        """Create handler instance."""
        return GetAnalysisStatusCommandHandler(
            analysis_repository=mock_analysis_repository
        )
    
    @pytest.mark.asyncio
    async def test_get_status_completed(
        self,
        handler,
        mock_completed_session
    ):
        """Test getting status of completed analysis."""
        # Arrange
        command = GetAnalysisStatusCommand(
            analysis_session_id=mock_completed_session.id
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert result.data["status"] == "completed"
        assert result.data["strategy"] == mock_completed_session.result
        assert result.data["calculation_time_ms"] == 1500
    
    @pytest.mark.asyncio
    async def test_get_status_processing(
        self,
        handler,
        mock_analysis_repository
    ):
        """Test getting status of processing analysis."""
        # Arrange
        processing_session = Mock(spec=AnalysisSession)
        processing_session.id = uuid4()
        processing_session.status = SessionStatus.RUNNING
        processing_session.created_at = datetime.utcnow()
        processing_session.started_at = datetime.utcnow()
        processing_session.analysis_type = "monte_carlo"
        
        mock_analysis_repository.get_by_id = AsyncMock(
            return_value=processing_session
        )
        
        command = GetAnalysisStatusCommand(
            analysis_session_id=processing_session.id
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert result.data["status"] == "processing"
        assert "progress_percentage" in result.data


class TestBatchAnalysisCommandHandler:
    """Test BatchAnalysisCommand handler."""
    
    @pytest.fixture
    def mock_positions(self):
        """Create mock positions."""
        positions = []
        for i in range(3):
            pos = Mock(spec=Position)
            pos.remaining_cards = list(range(30))
            pos.players_hands = {"player1": [], "player2": []}
            positions.append(pos)
        return positions
    
    @pytest.fixture
    def mock_analysis_repository(self):
        """Create mock analysis repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_request_handler(self):
        """Create mock request analysis handler."""
        handler = AsyncMock()
        # Return successful results with session IDs
        handler.handle = AsyncMock(side_effect=lambda cmd: Mock(
            success=True,
            data={"session_id": str(uuid4())}
        ))
        return handler
    
    @pytest.fixture
    def handler(
        self,
        mock_analysis_repository,
        mock_request_handler
    ):
        """Create handler instance."""
        return BatchAnalysisCommandHandler(
            analysis_repository=mock_analysis_repository,
            request_handler=mock_request_handler
        )
    
    @pytest.mark.asyncio
    async def test_batch_analysis_success(
        self,
        handler,
        mock_positions
    ):
        """Test successful batch analysis."""
        # Arrange
        command = BatchAnalysisCommand(
            positions=mock_positions,
            analysis_type="optimal",
            max_parallel=2
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert result.data["total_positions"] == 3
        assert result.data["sessions_created"] == 3
        assert len(result.data["session_ids"]) == 3


class TestCompareStrategiesCommandHandler:
    """Test CompareStrategiesCommand handler."""
    
    @pytest.fixture
    def mock_position(self):
        """Create mock position."""
        position = Mock(spec=Position)
        position.get_hash = Mock(return_value="position_hash_456")
        return position
    
    @pytest.fixture
    def mock_strategy_calculator(self):
        """Create mock strategy calculator."""
        calculator = AsyncMock()
        
        # Different strategies with different EVs
        optimal_strategy = Mock(spec=Strategy)
        optimal_strategy.expected_value = ExpectedValue(12.5)
        optimal_strategy.confidence = 0.99
        optimal_strategy.calculation_method = "optimal"
        
        heuristic_strategy = Mock(spec=Strategy)
        heuristic_strategy.expected_value = ExpectedValue(11.0)
        heuristic_strategy.confidence = 0.75
        heuristic_strategy.calculation_method = "heuristic"
        
        calculator.calculate_optimal_strategy = AsyncMock(
            return_value=optimal_strategy
        )
        calculator.calculate_heuristic_strategy = AsyncMock(
            return_value=heuristic_strategy
        )
        
        return calculator
    
    @pytest.fixture
    def mock_monte_carlo_simulator(self):
        """Create mock Monte Carlo simulator."""
        simulator = AsyncMock()
        
        mc_strategy = Mock(spec=Strategy)
        mc_strategy.expected_value = ExpectedValue(12.2)
        mc_strategy.confidence = 0.90
        mc_strategy.calculation_method = "monte_carlo"
        
        simulator.simulate_position = AsyncMock(return_value=mc_strategy)
        return simulator
    
    @pytest.fixture
    def handler(
        self,
        mock_strategy_calculator,
        mock_monte_carlo_simulator,
        mock_cache_manager
    ):
        """Create handler instance."""
        return CompareStrategiesCommandHandler(
            strategy_calculator=mock_strategy_calculator,
            monte_carlo_simulator=mock_monte_carlo_simulator,
            cache_manager=mock_cache_manager
        )
    
    @pytest.mark.asyncio
    async def test_compare_strategies_success(
        self,
        handler,
        mock_position
    ):
        """Test successful strategy comparison."""
        # Arrange
        command = CompareStrategiesCommand(
            position=mock_position,
            strategies_to_compare=["optimal", "monte_carlo", "heuristic"]
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert len(result.data["comparisons"]) == 3
        assert result.data["best_strategy"] == "optimal"
        assert all(
            strategy in result.data["comparisons"]
            for strategy in ["optimal", "monte_carlo", "heuristic"]
        )