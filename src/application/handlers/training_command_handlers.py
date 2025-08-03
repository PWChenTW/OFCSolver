"""Command handlers for training-related operations."""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from ..commands.base import CommandHandler, CommandResult
from ..commands.training_commands import (
    StartTrainingSessionCommand,
    SubmitTrainingMoveCommand,
    RequestHintCommand,
    CompleteScenarioCommand,
    AdjustDifficultyCommand,
    GenerateCustomScenarioCommand,
    ReviewTrainingHistoryCommand,
    EndTrainingSessionCommand
)
from ...domain.entities.training.training_session import TrainingSession
from ...domain.entities.training.scenario import Scenario
from ...domain.repositories.training_repository import TrainingRepository
from ...domain.repositories.scenario_repository import ScenarioRepository
from ...domain.services.scenario_generator import ScenarioGenerator
from ...domain.services.adaptive_difficulty import AdaptiveDifficulty
from ...domain.services.performance_tracker import PerformanceTracker
from ...domain.services.strategy_calculator import StrategyCalculator
from ...domain.value_objects.feedback import Feedback, FeedbackLevel
from ...domain.value_objects.performance import Performance
from ...domain.events.training_events import (
    TrainingSessionStartedEvent,
    ScenarioCompletedEvent,
    TrainingSessionEndedEvent
)


logger = logging.getLogger(__name__)


class StartTrainingSessionCommandHandler(CommandHandler[CommandResult]):
    """Handler for starting a new training session."""
    
    def __init__(
        self,
        training_repository: TrainingRepository,
        scenario_generator: ScenarioGenerator,
        adaptive_difficulty: AdaptiveDifficulty
    ):
        self.training_repository = training_repository
        self.scenario_generator = scenario_generator
        self.adaptive_difficulty = adaptive_difficulty
    
    async def handle(self, command: StartTrainingSessionCommand) -> CommandResult:
        """Start a new training session."""
        try:
            # Create training session
            session = TrainingSession.create(
                user_id=command.user_id,
                difficulty=command.difficulty,
                scenario_type=command.scenario_type,
                focus_areas=command.focus_areas
            )
            
            # Set time limit if specified
            if command.time_limit_minutes:
                session.set_time_limit(command.time_limit_minutes)
            
            # Generate initial scenario
            scenario = await self.scenario_generator.generate_scenario(
                difficulty=command.difficulty,
                scenario_type=command.scenario_type,
                focus_areas=command.focus_areas
            )
            
            # Add scenario to session
            session.add_scenario(scenario)
            
            # Save session and scenario
            await self.training_repository.save(session)
            
            # Publish domain event
            session.add_event(TrainingSessionStartedEvent(
                session_id=session.id,
                user_id=command.user_id,
                difficulty=command.difficulty,
                timestamp=command.timestamp
            ))
            
            logger.info(f"Training session started: {session.id}")
            
            return CommandResult.ok(
                data={
                    "session_id": str(session.id),
                    "scenario_id": str(scenario.id),
                    "initial_position": scenario.initial_position,
                    "instructions": scenario.instructions
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to start training session: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )


class SubmitTrainingMoveCommandHandler(CommandHandler[CommandResult]):
    """Handler for submitting moves in training scenarios."""
    
    def __init__(
        self,
        training_repository: TrainingRepository,
        scenario_repository: ScenarioRepository,
        strategy_calculator: StrategyCalculator,
        performance_tracker: PerformanceTracker
    ):
        self.training_repository = training_repository
        self.scenario_repository = scenario_repository
        self.strategy_calculator = strategy_calculator
        self.performance_tracker = performance_tracker
    
    async def handle(self, command: SubmitTrainingMoveCommand) -> CommandResult:
        """Submit a move in a training scenario."""
        try:
            # Load session and scenario
            session = await self.training_repository.get_by_id(command.session_id)
            if not session:
                return CommandResult.fail(
                    "Training session not found",
                    command.command_id
                )
            
            scenario = session.get_current_scenario()
            if not scenario or scenario.id != command.scenario_id:
                return CommandResult.fail(
                    "Scenario not found or not current",
                    command.command_id
                )
            
            # Record the move
            scenario.add_move(
                card=command.card,
                position=command.position,
                time_taken=command.time_taken_seconds
            )
            
            # Calculate optimal move for comparison
            optimal_strategy = await self.strategy_calculator.calculate_optimal_strategy(
                position=scenario.current_position,
                calculation_depth=3
            )
            
            # Evaluate the move
            move_quality = await self._evaluate_move(
                submitted_move=(command.card, command.position),
                optimal_strategy=optimal_strategy,
                time_taken=command.time_taken_seconds
            )
            
            # Update scenario state
            scenario.apply_move(command.card, command.position)
            
            # Track performance
            await self.performance_tracker.track_move(
                session_id=command.session_id,
                scenario_id=command.scenario_id,
                move_quality=move_quality,
                time_taken=command.time_taken_seconds
            )
            
            # Save updated session
            await self.training_repository.save(session)
            
            logger.info(
                f"Move submitted in training session {session.id}: "
                f"{command.card} at {command.position}"
            )
            
            return CommandResult.ok(
                data={
                    "move_quality": move_quality,
                    "is_scenario_complete": scenario.is_complete(),
                    "current_position": scenario.current_position
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to submit training move: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )
    
    async def _evaluate_move(
        self,
        submitted_move: tuple,
        optimal_strategy: Any,
        time_taken: float
    ) -> float:
        """Evaluate move quality (0.0 to 1.0)."""
        # Compare with optimal move
        optimal_move = optimal_strategy.recommended_moves[0]
        
        if submitted_move == (optimal_move.card, optimal_move.position):
            quality = 1.0
        else:
            # Check if it's in alternative moves
            for alt in optimal_strategy.alternative_moves:
                if submitted_move == (alt.move.card, alt.move.position):
                    # Scale quality based on EV difference
                    ev_ratio = alt.expected_value.value / optimal_move.expected_value.value
                    quality = max(0.5, min(0.95, ev_ratio))
                    break
            else:
                # Not in recommended moves
                quality = 0.3
        
        # Adjust for time taken (bonus for quick good moves)
        if quality > 0.8 and time_taken < 10:
            quality = min(1.0, quality * 1.1)
        
        return quality


class RequestHintCommandHandler(CommandHandler[CommandResult]):
    """Handler for requesting hints during training."""
    
    def __init__(
        self,
        training_repository: TrainingRepository,
        strategy_calculator: StrategyCalculator
    ):
        self.training_repository = training_repository
        self.strategy_calculator = strategy_calculator
    
    async def handle(self, command: RequestHintCommand) -> CommandResult:
        """Provide a hint for the current training scenario."""
        try:
            # Load session
            session = await self.training_repository.get_by_id(command.session_id)
            if not session:
                return CommandResult.fail(
                    "Training session not found",
                    command.command_id
                )
            
            scenario = session.get_current_scenario()
            if not scenario or scenario.id != command.scenario_id:
                return CommandResult.fail(
                    "Scenario not found or not current",
                    command.command_id
                )
            
            # Calculate optimal strategy
            optimal_strategy = await self.strategy_calculator.calculate_optimal_strategy(
                position=scenario.current_position,
                calculation_depth=3
            )
            
            # Generate hint based on level
            hint = self._generate_hint(
                optimal_strategy=optimal_strategy,
                hint_level=command.hint_level,
                current_position=scenario.current_position
            )
            
            # Record hint usage
            scenario.record_hint_usage(command.hint_level)
            
            # Save updated session
            await self.training_repository.save(session)
            
            logger.info(
                f"Hint requested for training session {session.id}, "
                f"level {command.hint_level}"
            )
            
            return CommandResult.ok(
                data={
                    "hint": hint,
                    "hint_level": command.hint_level,
                    "hints_used": scenario.hints_used
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to provide hint: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )
    
    def _generate_hint(
        self,
        optimal_strategy: Any,
        hint_level: int,
        current_position: Any
    ) -> str:
        """Generate hint based on level."""
        optimal_move = optimal_strategy.recommended_moves[0]
        
        if hint_level == 1:  # Subtle
            return (
                "Consider the strength progression rule - your bottom hand "
                "must be stronger than your middle hand."
            )
        elif hint_level == 2:  # Moderate
            return (
                f"The optimal move involves placing a "
                f"{optimal_move.card.rank.name} in the {optimal_move.position.row} row."
            )
        else:  # Explicit
            return (
                f"Place {optimal_move.card} at {optimal_move.position}. "
                f"This gives an expected value of {optimal_move.expected_value.value:.2f}."
            )


class CompleteScenarioCommandHandler(CommandHandler[CommandResult]):
    """Handler for completing training scenarios."""
    
    def __init__(
        self,
        training_repository: TrainingRepository,
        performance_tracker: PerformanceTracker,
        scenario_generator: ScenarioGenerator,
        adaptive_difficulty: AdaptiveDifficulty
    ):
        self.training_repository = training_repository
        self.performance_tracker = performance_tracker
        self.scenario_generator = scenario_generator
        self.adaptive_difficulty = adaptive_difficulty
    
    async def handle(self, command: CompleteScenarioCommand) -> CommandResult:
        """Complete a training scenario and generate feedback."""
        try:
            # Load session
            session = await self.training_repository.get_by_id(command.session_id)
            if not session:
                return CommandResult.fail(
                    "Training session not found",
                    command.command_id
                )
            
            scenario = session.get_scenario(command.scenario_id)
            if not scenario:
                return CommandResult.fail(
                    "Scenario not found",
                    command.command_id
                )
            
            # Calculate performance
            performance = await self.performance_tracker.calculate_scenario_performance(
                session_id=command.session_id,
                scenario_id=command.scenario_id
            )
            
            # Generate feedback
            feedback = self._generate_feedback(scenario, performance)
            
            # Complete the scenario
            scenario.complete(performance, feedback)
            
            # Check if difficulty adjustment needed
            new_difficulty = await self.adaptive_difficulty.calculate_new_difficulty(
                current_difficulty=session.current_difficulty,
                recent_performance=performance
            )
            
            if new_difficulty != session.current_difficulty:
                session.adjust_difficulty(new_difficulty)
            
            # Generate next scenario if session continues
            next_scenario = None
            if not session.is_time_limit_exceeded():
                next_scenario = await self.scenario_generator.generate_scenario(
                    difficulty=session.current_difficulty,
                    scenario_type=session.scenario_type,
                    focus_areas=session.focus_areas,
                    previous_scenarios=[s.id for s in session.scenarios]
                )
                session.add_scenario(next_scenario)
            
            # Save updated session
            await self.training_repository.save(session)
            
            # Publish domain event
            session.add_event(ScenarioCompletedEvent(
                session_id=session.id,
                scenario_id=scenario.id,
                performance=performance,
                timestamp=command.timestamp
            ))
            
            logger.info(f"Scenario completed in training session {session.id}")
            
            return CommandResult.ok(
                data={
                    "performance": performance,
                    "feedback": feedback,
                    "difficulty_adjusted": new_difficulty != session.current_difficulty,
                    "new_difficulty": new_difficulty.value if new_difficulty else None,
                    "next_scenario_id": str(next_scenario.id) if next_scenario else None
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to complete scenario: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )
    
    def _generate_feedback(self, scenario: Scenario, performance: Performance) -> Feedback:
        """Generate detailed feedback for the completed scenario."""
        strengths = []
        weaknesses = []
        suggestions = []
        
        # Analyze performance
        if performance.accuracy > 0.8:
            strengths.append("Excellent move selection accuracy")
        elif performance.accuracy < 0.5:
            weaknesses.append("Move selection needs improvement")
        
        if performance.average_time < 15:
            strengths.append("Quick decision making")
        elif performance.average_time > 60:
            weaknesses.append("Consider faster decision making")
        
        if scenario.hints_used == 0 and performance.accuracy > 0.7:
            strengths.append("Good independent problem solving")
        elif scenario.hints_used > 2:
            suggestions.append("Try to rely less on hints")
        
        # Overall assessment
        if performance.overall_score > 0.8:
            level = FeedbackLevel.EXCELLENT
            message = "Outstanding performance! You're mastering this difficulty level."
        elif performance.overall_score > 0.6:
            level = FeedbackLevel.GOOD
            message = "Good job! Keep practicing to improve consistency."
        else:
            level = FeedbackLevel.NEEDS_IMPROVEMENT
            message = "Keep practicing. Focus on understanding hand strength progression."
        
        return Feedback(
            level=level,
            message=message,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )


class EndTrainingSessionCommandHandler(CommandHandler[CommandResult]):
    """Handler for ending training sessions."""
    
    def __init__(
        self,
        training_repository: TrainingRepository,
        performance_tracker: PerformanceTracker
    ):
        self.training_repository = training_repository
        self.performance_tracker = performance_tracker
    
    async def handle(self, command: EndTrainingSessionCommand) -> CommandResult:
        """End a training session."""
        try:
            # Load session
            session = await self.training_repository.get_by_id(command.session_id)
            if not session:
                return CommandResult.fail(
                    "Training session not found",
                    command.command_id
                )
            
            # Calculate overall session performance
            session_performance = await self.performance_tracker.calculate_session_performance(
                session_id=command.session_id
            )
            
            # End the session
            session.end_session(save_progress=command.save_progress)
            
            # Save session
            await self.training_repository.save(session)
            
            # Publish domain event
            session.add_event(TrainingSessionEndedEvent(
                session_id=session.id,
                user_id=session.user_id,
                total_scenarios=len(session.scenarios),
                overall_performance=session_performance,
                timestamp=command.timestamp
            ))
            
            logger.info(f"Training session ended: {session.id}")
            
            return CommandResult.ok(
                data={
                    "session_id": str(session.id),
                    "total_scenarios": len(session.scenarios),
                    "session_duration_minutes": session.get_duration_minutes(),
                    "overall_performance": session_performance,
                    "progress_saved": command.save_progress
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to end training session: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )