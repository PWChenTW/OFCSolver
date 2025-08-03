"""Command handlers for analysis-related operations."""
import asyncio
import logging
from typing import List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from ..commands.base import CommandHandler, CommandResult
from ..commands.analysis_commands import (
    RequestAnalysisCommand,
    CancelAnalysisCommand,
    GetAnalysisStatusCommand,
    BatchAnalysisCommand,
    CompareStrategiesCommand,
    SaveAnalysisResultCommand
)
from ...domain.entities.strategy.analysis_session import AnalysisSession, AnalysisStatus
from ...domain.repositories.analysis_repository import AnalysisRepository
from ...domain.repositories.position_repository import PositionRepository
from ...domain.services.strategy_calculator import StrategyCalculator
from ...domain.services.monte_carlo_simulator import MonteCarloSimulator
from ...domain.value_objects.strategy import Strategy
from ...domain.events.strategy_events import (
    AnalysisRequestedEvent,
    AnalysisCompletedEvent,
    AnalysisCancelledEvent
)
from ...infrastructure.cache.cache_manager import CacheManager


logger = logging.getLogger(__name__)


class RequestAnalysisCommandHandler(CommandHandler[CommandResult]):
    """Handler for requesting strategy analysis."""
    
    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        position_repository: PositionRepository,
        strategy_calculator: StrategyCalculator,
        monte_carlo_simulator: MonteCarloSimulator,
        cache_manager: CacheManager
    ):
        self.analysis_repository = analysis_repository
        self.position_repository = position_repository
        self.strategy_calculator = strategy_calculator
        self.monte_carlo_simulator = monte_carlo_simulator
        self.cache_manager = cache_manager
    
    async def handle(self, command: RequestAnalysisCommand) -> CommandResult:
        """Request strategy analysis for a position."""
        try:
            # Check cache first if not forcing recalculation
            if not command.force_recalculate:
                cached_strategy = await self.cache_manager.get_strategy(command.position)
                if cached_strategy:
                    logger.info(f"Returning cached strategy for position")
                    return CommandResult.ok(
                        data={
                            "strategy": cached_strategy,
                            "cache_hit": True,
                            "session_id": None
                        },
                        command_id=command.command_id
                    )
            
            # Create analysis session
            session = AnalysisSession.create(
                position=command.position,
                analysis_type=command.analysis_type,
                calculation_depth=command.calculation_depth,
                priority=command.priority
            )
            
            # Save the session
            await self.analysis_repository.save(session)
            
            # Save the position for reference
            await self.position_repository.save(command.position)
            
            # Publish domain event
            session.add_event(AnalysisRequestedEvent(
                session_id=session.id,
                position=command.position,
                analysis_type=command.analysis_type,
                timestamp=command.timestamp
            ))
            
            # Start async calculation
            asyncio.create_task(self._perform_analysis(
                session=session,
                command=command
            ))
            
            logger.info(f"Analysis requested: Session {session.id}")
            
            return CommandResult.ok(
                data={
                    "session_id": str(session.id),
                    "status": "processing",
                    "estimated_time_seconds": self._estimate_calculation_time(command)
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to request analysis: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )
    
    async def _perform_analysis(
        self,
        session: AnalysisSession,
        command: RequestAnalysisCommand
    ) -> None:
        """Perform the actual analysis asynchronously."""
        try:
            session.start_calculation()
            
            # Select calculation method
            if command.analysis_type == "optimal":
                strategy = await self.strategy_calculator.calculate_optimal_strategy(
                    position=command.position,
                    calculation_depth=command.calculation_depth
                )
            elif command.analysis_type == "monte_carlo":
                strategy = await self.monte_carlo_simulator.simulate_position(
                    position=command.position,
                    num_simulations=50000
                )
            else:  # heuristic
                strategy = await self.strategy_calculator.calculate_heuristic_strategy(
                    position=command.position
                )
            
            # Update session with results
            session.complete_calculation(strategy)
            await self.analysis_repository.save(session)
            
            # Cache the result
            await self.cache_manager.store_strategy(command.position, strategy)
            
            # Publish completion event
            session.add_event(AnalysisCompletedEvent(
                session_id=session.id,
                strategy=strategy,
                calculation_time_ms=session.calculation_time_ms,
                timestamp=datetime.utcnow()
            ))
            
            logger.info(f"Analysis completed: Session {session.id}")
            
        except asyncio.TimeoutError:
            session.fail_calculation("Calculation timeout")
            await self.analysis_repository.save(session)
            logger.error(f"Analysis timeout: Session {session.id}")
        except Exception as e:
            session.fail_calculation(str(e))
            await self.analysis_repository.save(session)
            logger.error(f"Analysis failed: Session {session.id} - {str(e)}")
    
    def _estimate_calculation_time(self, command: RequestAnalysisCommand) -> int:
        """Estimate calculation time in seconds."""
        base_time = {
            "heuristic": 1,
            "monte_carlo": 10,
            "optimal": 30
        }
        
        time_estimate = base_time.get(command.analysis_type, 10)
        
        # Adjust for calculation depth
        if command.analysis_type == "optimal":
            time_estimate *= (command.calculation_depth / 3)
        
        # Adjust for position complexity
        remaining_cards = len(command.position.remaining_cards)
        if remaining_cards > 30:
            time_estimate *= 1.5
        elif remaining_cards < 10:
            time_estimate *= 0.5
        
        return int(time_estimate)


class CancelAnalysisCommandHandler(CommandHandler[CommandResult]):
    """Handler for cancelling ongoing analysis."""
    
    def __init__(self, analysis_repository: AnalysisRepository):
        self.analysis_repository = analysis_repository
    
    async def handle(self, command: CancelAnalysisCommand) -> CommandResult:
        """Cancel an ongoing analysis."""
        try:
            # Load the analysis session
            session = await self.analysis_repository.get_by_id(command.analysis_session_id)
            if not session:
                return CommandResult.fail(
                    "Analysis session not found",
                    command.command_id
                )
            
            # Check if can be cancelled
            if session.status != AnalysisStatus.PROCESSING:
                return CommandResult.fail(
                    f"Cannot cancel analysis in status: {session.status}",
                    command.command_id
                )
            
            # Cancel the session
            session.cancel_calculation(command.reason or "User requested cancellation")
            await self.analysis_repository.save(session)
            
            # Publish cancellation event
            session.add_event(AnalysisCancelledEvent(
                session_id=session.id,
                reason=command.reason,
                timestamp=command.timestamp
            ))
            
            logger.info(f"Analysis cancelled: Session {session.id}")
            
            return CommandResult.ok(
                data={
                    "session_id": str(session.id),
                    "status": "cancelled"
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to cancel analysis: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )


class GetAnalysisStatusCommandHandler(CommandHandler[CommandResult]):
    """Handler for getting analysis status."""
    
    def __init__(self, analysis_repository: AnalysisRepository):
        self.analysis_repository = analysis_repository
    
    async def handle(self, command: GetAnalysisStatusCommand) -> CommandResult:
        """Get the status of an analysis session."""
        try:
            # Load the analysis session
            session = await self.analysis_repository.get_by_id(command.analysis_session_id)
            if not session:
                return CommandResult.fail(
                    "Analysis session not found",
                    command.command_id
                )
            
            # Prepare response data
            data = {
                "session_id": str(session.id),
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "analysis_type": session.analysis_type
            }
            
            if session.status == AnalysisStatus.COMPLETED:
                data.update({
                    "strategy": session.result,
                    "calculation_time_ms": session.calculation_time_ms,
                    "completed_at": session.completed_at.isoformat()
                })
            elif session.status == AnalysisStatus.FAILED:
                data.update({
                    "error": session.error_message,
                    "failed_at": session.completed_at.isoformat()
                })
            elif session.status == AnalysisStatus.PROCESSING:
                # Estimate progress
                elapsed = (datetime.utcnow() - session.started_at).total_seconds()
                data["progress_percentage"] = min(95, int(elapsed * 10))  # Simple estimate
            
            return CommandResult.ok(
                data=data,
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to get analysis status: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )


class BatchAnalysisCommandHandler(CommandHandler[CommandResult]):
    """Handler for batch analysis requests."""
    
    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        request_handler: RequestAnalysisCommandHandler
    ):
        self.analysis_repository = analysis_repository
        self.request_handler = request_handler
    
    async def handle(self, command: BatchAnalysisCommand) -> CommandResult:
        """Process batch analysis requests."""
        try:
            session_ids = []
            
            # Create individual analysis requests with rate limiting
            semaphore = asyncio.Semaphore(command.max_parallel)
            
            async def process_position(position):
                async with semaphore:
                    individual_command = RequestAnalysisCommand(
                        position=position,
                        analysis_type=command.analysis_type,
                        priority=command.priority,
                        user_id=command.user_id
                    )
                    result = await self.request_handler.handle(individual_command)
                    if result.success and result.data.get("session_id"):
                        return result.data["session_id"]
                    return None
            
            # Process all positions
            tasks = [process_position(pos) for pos in command.positions]
            results = await asyncio.gather(*tasks)
            
            # Filter out None results
            session_ids = [sid for sid in results if sid is not None]
            
            logger.info(
                f"Batch analysis started: {len(session_ids)} sessions created "
                f"out of {len(command.positions)} positions"
            )
            
            return CommandResult.ok(
                data={
                    "batch_id": str(uuid4()),
                    "session_ids": session_ids,
                    "total_positions": len(command.positions),
                    "sessions_created": len(session_ids)
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to process batch analysis: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )


class CompareStrategiesCommandHandler(CommandHandler[CommandResult]):
    """Handler for comparing different strategies."""
    
    def __init__(
        self,
        strategy_calculator: StrategyCalculator,
        monte_carlo_simulator: MonteCarloSimulator,
        cache_manager: CacheManager
    ):
        self.strategy_calculator = strategy_calculator
        self.monte_carlo_simulator = monte_carlo_simulator
        self.cache_manager = cache_manager
    
    async def handle(self, command: CompareStrategiesCommand) -> CommandResult:
        """Compare multiple strategies for a position."""
        try:
            comparisons = {}
            
            # Calculate each strategy
            for strategy_type in command.strategies_to_compare:
                if strategy_type == "optimal":
                    strategy = await self.strategy_calculator.calculate_optimal_strategy(
                        position=command.position,
                        calculation_depth=3
                    )
                elif strategy_type == "monte_carlo":
                    strategy = await self.monte_carlo_simulator.simulate_position(
                        position=command.position,
                        num_simulations=10000
                    )
                elif strategy_type == "heuristic":
                    strategy = await self.strategy_calculator.calculate_heuristic_strategy(
                        position=command.position
                    )
                else:
                    continue
                
                comparisons[strategy_type] = {
                    "strategy": strategy,
                    "expected_value": strategy.expected_value.value,
                    "confidence": strategy.confidence,
                    "calculation_method": strategy.calculation_method
                }
            
            # Find best strategy
            best_strategy = max(
                comparisons.items(),
                key=lambda x: x[1]["expected_value"]
            )
            
            logger.info(
                f"Strategy comparison completed for {len(comparisons)} strategies"
            )
            
            return CommandResult.ok(
                data={
                    "comparisons": comparisons,
                    "best_strategy": best_strategy[0],
                    "position_hash": command.position.get_hash()
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to compare strategies: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )