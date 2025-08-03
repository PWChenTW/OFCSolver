"""
Game Validator Domain Service

Service for validating game rules, card placements, and game state
according to OFC rules and multi-player game logic.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..base import DomainService
from ..entities.game import Game
from ..entities.game.player import Player, PlayerId, PlayerStatus
from ..exceptions import GameStateError, InvalidCardPlacementError
from ..value_objects import Card, CardPosition
from .hand_evaluator import HandEvaluator


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    error_message: Optional[str] = None
    warning_message: Optional[str] = None


class GameValidator(DomainService):
    """
    Domain service for game validation operations.

    Validates all aspects of OFC game rules including card placement,
    row strength progression, turn order, and game completion.
    """

    def __init__(self):
        """Initialize game validator with dependencies."""
        self._hand_evaluator = HandEvaluator()

    def validate_card_placement(
        self, game: Game, player_id: PlayerId, card: Card, position: CardPosition
    ) -> ValidationResult:
        """
        Validate if a card can be placed at the specified position.

        Args:
            game: Game instance
            player_id: ID of player placing the card
            card: Card to place
            position: Position where card should be placed

        Returns:
            ValidationResult indicating if placement is valid
        """
        # Check basic game state
        if game.is_completed:
            return ValidationResult(
                is_valid=False, error_message="Cannot place cards in completed game"
            )

        # Get player first to check if they exist
        player = self._get_player_by_id(game, player_id)
        if not player:
            return ValidationResult(
                is_valid=False, error_message=f"Player {player_id} not in game"
            )

        # Check if it's player's turn
        current_player = game.get_current_player()
        if player_id != current_player.id:
            return ValidationResult(
                is_valid=False, error_message=f"It's not player {player_id}'s turn"
            )

        # Check if player has the card
        if card not in player.hand_cards:
            return ValidationResult(
                is_valid=False,
                error_message=f"Player {player_id} does not have card {card}",
            )

        # Check position capacity
        if not player.can_place_card(card, position):
            max_cards = position.max_cards
            current_cards = len(player.get_row_cards(position))
            if current_cards >= max_cards:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"{position.display_name} is full ({current_cards}/{max_cards})",
                )

        # Check for duplicate cards in game
        if self._is_card_already_placed(game, card):
            return ValidationResult(
                is_valid=False,
                error_message=f"Card {card} is already placed in the game",
            )

        return ValidationResult(is_valid=True)

    def validate_row_strength_progression(self, player: Player) -> ValidationResult:
        """
        Validate OFC row strength progression (bottom > middle > top).

        Args:
            player: Player to validate

        Returns:
            ValidationResult indicating if progression is valid
        """
        # Only validate if player has complete rows
        if not player.is_layout_complete():
            return ValidationResult(
                is_valid=True,
                warning_message="Player layout not complete, skipping progression validation",
            )

        # Check if player is already fouled
        if player.status == PlayerStatus.FOULED:
            return ValidationResult(
                is_valid=False, error_message="Player has fouled hand"
            )

        top_cards = player.top_row
        middle_cards = player.middle_row
        bottom_cards = player.bottom_row

        # Validate card counts
        if len(top_cards) != 3 or len(middle_cards) != 5 or len(bottom_cards) != 5:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid card counts: top={len(top_cards)}, middle={len(middle_cards)}, bottom={len(bottom_cards)}",
            )

        # Use hand evaluator to check progression
        is_valid = self._hand_evaluator.validate_ofc_progression(
            top_cards, middle_cards, bottom_cards
        )

        if not is_valid:
            return ValidationResult(
                is_valid=False,
                error_message="Hand violates OFC progression rules (bottom > middle > top)",
            )

        return ValidationResult(is_valid=True)

    def check_game_completion(self, game: Game) -> ValidationResult:
        """
        Check if game is ready for completion.

        Args:
            game: Game to check

        Returns:
            ValidationResult indicating if game can be completed
        """
        if game.is_completed:
            return ValidationResult(
                is_valid=True, warning_message="Game is already completed"
            )

        # Check if all players have placed all cards
        incomplete_players = []
        for player in game.players:
            if not player.is_layout_complete():
                incomplete_players.append(player.name)

        if incomplete_players:
            return ValidationResult(
                is_valid=False,
                error_message=f"Players still need to complete layouts: {', '.join(incomplete_players)}",
            )

        # Check total cards placed
        total_cards = sum(player.total_cards_placed for player in game.players)
        expected_cards = len(game.players) * 13

        if total_cards != expected_cards:
            return ValidationResult(
                is_valid=False,
                error_message=f"Card count mismatch: {total_cards} placed, {expected_cards} expected",
            )

        return ValidationResult(is_valid=True)

    def validate_turn_order(self, game: Game, player_id: PlayerId) -> ValidationResult:
        """
        Validate if it's the specified player's turn.

        Args:
            game: Game instance
            player_id: ID of player to check

        Returns:
            ValidationResult indicating if it's player's turn
        """
        if game.is_completed:
            return ValidationResult(
                is_valid=False, error_message="Game is completed, no more turns"
            )

        current_player = game.get_current_player()
        if current_player.id != player_id:
            return ValidationResult(
                is_valid=False,
                error_message=f"It's {current_player.name}'s turn, not player {player_id}",
            )

        return ValidationResult(is_valid=True)

    def validate_multi_player_game_state(self, game: Game) -> ValidationResult:
        """
        Validate overall multi-player game state consistency.

        Args:
            game: Game to validate

        Returns:
            ValidationResult indicating if game state is consistent
        """
        # Check player count
        player_count = len(game.players)
        if player_count < 2 or player_count > 4:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid player count: {player_count} (must be 2-4)",
            )

        # Check for duplicate player IDs
        player_ids = [p.id for p in game.players]
        if len(set(player_ids)) != len(player_ids):
            return ValidationResult(
                is_valid=False, error_message="Duplicate player IDs found"
            )

        # Check card distribution
        all_placed_cards = []
        for player in game.players:
            placed_cards = player.top_row + player.middle_row + player.bottom_row
            all_placed_cards.extend(placed_cards)

        # Check for duplicate cards across players
        if len(all_placed_cards) != len(set(all_placed_cards)):
            return ValidationResult(
                is_valid=False, error_message="Duplicate cards found across players"
            )

        # Validate each player's layout progression if complete
        fouled_players = []
        for player in game.players:
            if player.is_layout_complete():
                result = self.validate_row_strength_progression(player)
                if not result.is_valid:
                    fouled_players.append(player.name)

        if fouled_players:
            return ValidationResult(
                is_valid=True,  # Game state is valid, but some players are fouled
                warning_message=f"Players with fouled hands: {', '.join(fouled_players)}",
            )

        return ValidationResult(is_valid=True)

    def can_place_card_safely(
        self, game: Game, player_id: PlayerId, card: Card, position: CardPosition
    ) -> ValidationResult:
        """
        Check if placing a card would result in a safe (non-fouling) placement.

        This is a helper method that simulates placement to check for potential fouling.

        Args:
            game: Game instance
            player_id: ID of player placing the card
            card: Card to place
            position: Position where card should be placed

        Returns:
            ValidationResult indicating if placement is safe
        """
        # First check basic placement validation
        basic_result = self.validate_card_placement(game, player_id, card, position)
        if not basic_result.is_valid:
            return basic_result

        player = self._get_player_by_id(game, player_id)
        if not player:
            return ValidationResult(
                is_valid=False, error_message=f"Player {player_id} not found"
            )

        # Simulate placement to check for potential fouling
        current_top = player.top_row.copy()
        current_middle = player.middle_row.copy()
        current_bottom = player.bottom_row.copy()

        # Add card to appropriate row
        if position == CardPosition.TOP:
            current_top.append(card)
        elif position == CardPosition.MIDDLE:
            current_middle.append(card)
        elif position == CardPosition.BOTTOM:
            current_bottom.append(card)

        # Check if this would create an immediate fouling situation
        # Only check if all affected rows have enough cards for comparison
        if (
            len(current_top) == 3
            and len(current_middle) >= 3
            and len(current_bottom) >= 3
        ):
            # Check if this placement would violate progression
            top_hand = self._hand_evaluator.evaluate_hand(current_top)
            middle_partial = self._hand_evaluator.evaluate_hand(
                current_middle[:3]
            )  # Compare with same number of cards

            if self._hand_evaluator.compare_hands(top_hand, middle_partial) > 0:
                return ValidationResult(
                    is_valid=True,  # Placement is technically valid
                    warning_message=f"Warning: Placing {card} at {position} may lead to fouling",
                )

        return ValidationResult(is_valid=True)

    def _get_player_by_id(self, game: Game, player_id: PlayerId) -> Optional[Player]:
        """Get player by ID from game."""
        for player in game.players:
            if player.id == player_id:
                return player
        return None

    def _is_card_already_placed(self, game: Game, card: Card) -> bool:
        """Check if card is already placed anywhere in the game."""
        for player in game.players:
            all_player_cards = player.top_row + player.middle_row + player.bottom_row
            if card in all_player_cards:
                return True
        return False

    def get_available_positions(
        self, game: Game, player_id: PlayerId
    ) -> List[CardPosition]:
        """
        Get list of positions where the current player can still place cards.

        Args:
            game: Game instance
            player_id: Player ID to check

        Returns:
            List of available positions
        """
        player = self._get_player_by_id(game, player_id)
        if not player:
            return []

        return player.get_available_positions()

    def get_validation_summary(self, game: Game) -> Dict[str, ValidationResult]:
        """
        Get comprehensive validation summary for the game.

        Args:
            game: Game to validate

        Returns:
            Dictionary of validation results for different aspects
        """
        summary = {}

        # Overall game state
        summary["game_state"] = self.validate_multi_player_game_state(game)

        # Game completion
        summary["completion"] = self.check_game_completion(game)

        # Individual player validations
        for player in game.players:
            player_key = f"player_{player.id}"
            summary[player_key] = self.validate_row_strength_progression(player)

        # Turn order (if game not completed)
        if not game.is_completed:
            current_player = game.get_current_player()
            summary["turn_order"] = self.validate_turn_order(game, current_player.id)

        return summary
