"""Command handlers module initialization."""
from typing import Dict, Type, Any

from ..commands.base import Command, CommandHandler
from ..commands.game_commands import (
    CreateGameCommand,
    PlaceCardCommand,
    StartFantasyLandCommand,
    CompleteRoundCommand,
    SetFantasyLandCommand
)
from ..commands.analysis_commands import (
    RequestAnalysisCommand,
    CancelAnalysisCommand,
    GetAnalysisStatusCommand,
    BatchAnalysisCommand,
    CompareStrategiesCommand
)
from ..commands.training_commands import (
    StartTrainingSessionCommand,
    SubmitTrainingMoveCommand,
    RequestHintCommand,
    CompleteScenarioCommand,
    EndTrainingSessionCommand
)

from .game_command_handlers import (
    CreateGameCommandHandler,
    PlaceCardCommandHandler,
    StartFantasyLandCommandHandler,
    CompleteRoundCommandHandler,
    SetFantasyLandCommandHandler
)
from .analysis_command_handlers import (
    RequestAnalysisCommandHandler,
    CancelAnalysisCommandHandler,
    GetAnalysisStatusCommandHandler,
    BatchAnalysisCommandHandler,
    CompareStrategiesCommandHandler
)
from .training_command_handlers import (
    StartTrainingSessionCommandHandler,
    SubmitTrainingMoveCommandHandler,
    RequestHintCommandHandler,
    CompleteScenarioCommandHandler,
    EndTrainingSessionCommandHandler
)


# Command to handler mapping
COMMAND_HANDLER_MAPPING: Dict[Type[Command], Type[CommandHandler]] = {
    # Game commands
    CreateGameCommand: CreateGameCommandHandler,
    PlaceCardCommand: PlaceCardCommandHandler,
    StartFantasyLandCommand: StartFantasyLandCommandHandler,
    CompleteRoundCommand: CompleteRoundCommandHandler,
    SetFantasyLandCommand: SetFantasyLandCommandHandler,
    
    # Analysis commands
    RequestAnalysisCommand: RequestAnalysisCommandHandler,
    CancelAnalysisCommand: CancelAnalysisCommandHandler,
    GetAnalysisStatusCommand: GetAnalysisStatusCommandHandler,
    BatchAnalysisCommand: BatchAnalysisCommandHandler,
    CompareStrategiesCommand: CompareStrategiesCommandHandler,
    
    # Training commands
    StartTrainingSessionCommand: StartTrainingSessionCommandHandler,
    SubmitTrainingMoveCommand: SubmitTrainingMoveCommandHandler,
    RequestHintCommand: RequestHintCommandHandler,
    CompleteScenarioCommand: CompleteScenarioCommandHandler,
    EndTrainingSessionCommand: EndTrainingSessionCommandHandler,
}


def get_handler_for_command(command_type: Type[Command]) -> Type[CommandHandler]:
    """Get the handler class for a command type."""
    return COMMAND_HANDLER_MAPPING.get(command_type)


__all__ = [
    # Game handlers
    'CreateGameCommandHandler',
    'PlaceCardCommandHandler',
    'StartFantasyLandCommandHandler',
    'CompleteRoundCommandHandler',
    'SetFantasyLandCommandHandler',
    
    # Analysis handlers
    'RequestAnalysisCommandHandler',
    'CancelAnalysisCommandHandler',
    'GetAnalysisStatusCommandHandler',
    'BatchAnalysisCommandHandler',
    'CompareStrategiesCommandHandler',
    
    # Training handlers
    'StartTrainingSessionCommandHandler',
    'SubmitTrainingMoveCommandHandler',
    'RequestHintCommandHandler',
    'CompleteScenarioCommandHandler',
    'EndTrainingSessionCommandHandler',
    
    # Utilities
    'COMMAND_HANDLER_MAPPING',
    'get_handler_for_command',
]