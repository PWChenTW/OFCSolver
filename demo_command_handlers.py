"""Demo script showing command handler usage."""
import asyncio
from uuid import uuid4
import logging

from src.application.services.command_bus import CommandBusBuilder
from src.application.commands.game_commands import (
    CreateGameCommand,
    PlaceCardCommand
)
from src.application.commands.analysis_commands import RequestAnalysisCommand
from src.application.handlers.game_command_handlers import (
    CreateGameCommandHandler,
    PlaceCardCommandHandler
)
from src.application.handlers.analysis_command_handlers import (
    RequestAnalysisCommandHandler
)
from src.application.validators.command_validators import (
    CreateGameCommandValidator,
    PlaceCardCommandValidator,
    RequestAnalysisCommandValidator
)
from src.domain.value_objects.game_rules import GameRules
from src.domain.value_objects.card import Card, Rank, Suit
from src.domain.value_objects.card_position import CardPosition
from src.domain.entities.game.position import Position

# Mock implementations for demo
class MockGameRepository:
    def __init__(self):
        self.games = {}
    
    async def save(self, game):
        self.games[game.id] = game
        print(f"✅ Game saved: {game.id}")
    
    async def get_by_id(self, game_id):
        return self.games.get(game_id)


class MockPlayerRepository:
    def __init__(self):
        self.players = {
            "player1": type('Player', (), {'id': 'player1', 'name': 'Alice'}),
            "player2": type('Player', (), {'id': 'player2', 'name': 'Bob'}),
        }
    
    async def get_by_id(self, player_id):
        return self.players.get(player_id)


class MockAnalysisRepository:
    async def save(self, session):
        print(f"✅ Analysis session saved: {session.id}")


class MockPositionRepository:
    async def save(self, position):
        print(f"✅ Position saved")


class MockStrategyCalculator:
    async def calculate_optimal_strategy(self, position, calculation_depth):
        print(f"🧮 Calculating optimal strategy with depth {calculation_depth}...")
        await asyncio.sleep(0.5)  # Simulate calculation
        return type('Strategy', (), {
            'expected_value': type('EV', (), {'value': 12.5}),
            'confidence': 0.95,
            'calculation_method': 'optimal',
            'recommended_moves': []
        })


class MockCacheManager:
    def __init__(self):
        self.cache = {}
    
    async def get_strategy(self, position):
        return None  # No cache for demo
    
    async def store_strategy(self, position, strategy):
        print(f"💾 Strategy cached")


class MockGameValidator:
    async def validate_card_placement(self, game, player_id, card, position):
        return type('ValidationResult', (), {
            'is_valid': True,
            'error_message': None
        })


async def demo_command_handlers():
    """Demonstrate command handler usage."""
    print("🎮 OFC Solver Command Handler Demo\n")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize repositories and services
    game_repo = MockGameRepository()
    player_repo = MockPlayerRepository()
    analysis_repo = MockAnalysisRepository()
    position_repo = MockPositionRepository()
    strategy_calc = MockStrategyCalculator()
    cache_manager = MockCacheManager()
    game_validator = MockGameValidator()
    
    # Build command bus
    print("🔧 Building command bus...")
    command_bus = (
        CommandBusBuilder()
        # Game handlers
        .with_handler(
            CreateGameCommand,
            CreateGameCommandHandler(game_repo, player_repo)
        )
        .with_validator(
            CreateGameCommand,
            CreateGameCommandValidator(player_repo)
        )
        .with_handler(
            PlaceCardCommand,
            PlaceCardCommandHandler(game_repo, game_validator)
        )
        .with_validator(
            PlaceCardCommand,
            PlaceCardCommandValidator(game_repo)
        )
        # Analysis handlers
        .with_handler(
            RequestAnalysisCommand,
            RequestAnalysisCommandHandler(
                analysis_repo,
                position_repo,
                strategy_calc,
                None,  # No Monte Carlo for demo
                cache_manager
            )
        )
        .with_validator(
            RequestAnalysisCommand,
            RequestAnalysisCommandValidator()
        )
        # Add middleware
        .with_logging()
        .build()
    )
    
    print("✅ Command bus ready!\n")
    
    # Demo 1: Create a game
    print("📋 Demo 1: Creating a new game")
    create_game_cmd = CreateGameCommand(
        player_ids=["player1", "player2"],
        rules=GameRules(),
        game_variant="standard"
    )
    
    result = await command_bus.execute(create_game_cmd)
    
    if result.success:
        game_id = result.data["game_id"]
        print(f"✅ Game created successfully! ID: {game_id}\n")
    else:
        print(f"❌ Failed to create game: {result.error}\n")
        return
    
    # Demo 2: Place a card (would fail without proper game setup)
    print("📋 Demo 2: Attempting to place a card")
    place_card_cmd = PlaceCardCommand(
        game_id=uuid4(),  # Using random ID for demo
        player_id="player1",
        card=Card(rank=Rank.ACE, suit=Suit.SPADES),
        position=CardPosition(row="bottom", index=0)
    )
    
    result = await command_bus.execute(place_card_cmd)
    
    if result.success:
        print(f"✅ Card placed successfully!\n")
    else:
        print(f"❌ Failed to place card: {result.error}\n")
    
    # Demo 3: Request strategy analysis
    print("📋 Demo 3: Requesting strategy analysis")
    
    # Create a mock position
    position = Position(
        game_id=uuid4(),
        players_hands={"player1": [], "player2": []},
        remaining_cards=list(range(52)),
        current_player="player1",
        round_number=1
    )
    
    analysis_cmd = RequestAnalysisCommand(
        position=position,
        analysis_type="optimal",
        calculation_depth=3,
        max_calculation_time_seconds=60,
        force_recalculate=True
    )
    
    result = await command_bus.execute(analysis_cmd)
    
    if result.success:
        print(f"✅ Analysis requested!")
        print(f"   Session ID: {result.data['session_id']}")
        print(f"   Status: {result.data['status']}")
        print(f"   Estimated time: {result.data['estimated_time_seconds']}s\n")
    else:
        print(f"❌ Failed to request analysis: {result.error}\n")
    
    # Demo 4: Invalid command (validation failure)
    print("📋 Demo 4: Testing validation - invalid player count")
    invalid_cmd = CreateGameCommand(
        player_ids=["player1"],  # Only 1 player (invalid)
        rules=GameRules(),
        game_variant="standard"
    )
    
    # This will trigger validation error
    try:
        result = await command_bus.execute(invalid_cmd)
    except ValueError as e:
        print(f"❌ Validation failed as expected: {e}\n")
    
    print("🎉 Demo completed!")


if __name__ == "__main__":
    asyncio.run(demo_command_handlers())