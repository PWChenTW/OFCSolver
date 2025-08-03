"""
Game Domain Exceptions

Exceptions specific to game management and gameplay.
"""

from typing import Optional

from .base_exceptions import (
    BusinessRuleViolationError,
    DomainError,
    ResourceNotFoundError,
)


class GameStateError(BusinessRuleViolationError):
    """Exception for invalid game state operations."""

    def __init__(self, message: str, game_id: Optional[str] = None):
        context = {"game_id": game_id} if game_id else None
        super().__init__("GAME_STATE", message, context)


class InvalidGameStateError(GameStateError):
    """Exception for invalid game state."""

    def __init__(self, message: str, game_id: Optional[str] = None):
        super().__init__(message, game_id)


class InvalidCardPlacementError(BusinessRuleViolationError):
    """Exception for invalid card placement attempts."""

    def __init__(
        self,
        message: str,
        card: Optional[str] = None,
        position: Optional[str] = None,
        player_id: Optional[str] = None,
    ):
        context = {"card": card, "position": position, "player_id": player_id}
        context = {k: v for k, v in context.items() if v is not None}
        super().__init__("CARD_PLACEMENT", message, context)


class PlayerNotFoundError(ResourceNotFoundError):
    """Exception for player not found errors."""

    def __init__(self, player_id: str, game_id: Optional[str] = None):
        context = {"game_id": game_id} if game_id else None
        super().__init__("Player", player_id, context)


class GameNotFoundError(ResourceNotFoundError):
    """Exception for game not found errors."""

    def __init__(self, game_id: str):
        super().__init__("Game", game_id)


class InvalidGameConfigurationError(DomainError):
    """Exception for invalid game configuration."""

    def __init__(self, message: str, config_field: Optional[str] = None):
        context = {"config_field": config_field} if config_field else None
        super().__init__(message, "INVALID_GAME_CONFIG", context)
