"""
Pineapple OFC Game Validator

Extends base game validator with Pineapple OFC specific rules.
MVP implementation focusing on essential validation only.
"""

from typing import List, Optional, Set
from uuid import UUID

from .game_validator import GameValidator, ValidationResult
from .pineapple_evaluator import PineappleHandEvaluator
from .pineapple_fantasy_land import PineappleFantasyLandManager
from ..entities.game import Game
from ..entities.game.player import Player, PlayerId
from ..value_objects import Card, PineappleAction, InitialPlacement, FantasyLandState
from ..value_objects.position import Position


class PineappleGameValidator(GameValidator):
    """
    Game validator for Pineapple OFC variant.
    
    Additional validations:
    - 3-pick-2 card selection
    - Fantasy Land state management
    - Discard tracking
    """
    
    def __init__(self):
        """Initialize with Pineapple-specific services."""
        super().__init__()
        self._hand_evaluator = PineappleHandEvaluator()
        self._fantasy_land_manager = PineappleFantasyLandManager(self._hand_evaluator)
        self._discarded_cards: Set[Card] = set()  # Track discarded cards
    
    def validate_pineapple_action(
        self,
        action: PineappleAction,
        player: Player,
        game_state: Game,
    ) -> ValidationResult:
        """
        Validate a Pineapple OFC 3-pick-2 action.
        
        Checks:
        - Player receives exactly 3 cards
        - Places exactly 2 cards
        - Discards exactly 1 card
        - All cards from dealt cards
        - No duplicate placements
        """
        # Check player turn
        if game_state.get_current_player().id != action.player_id:
            return ValidationResult(
                is_valid=False,
                error_message="Not player's turn"
            )
        
        # Validate card counts
        if len(action.dealt_cards) != 3:
            return ValidationResult(
                is_valid=False,
                error_message=f"Must deal 3 cards, got {len(action.dealt_cards)}"
            )
        
        if len(action.placements) != 2:
            return ValidationResult(
                is_valid=False,
                error_message=f"Must place 2 cards, got {len(action.placements)}"
            )
        
        # Validate cards match
        placed_cards = {card for card, _ in action.placements}
        all_action_cards = placed_cards | {action.discarded_card}
        dealt_set = set(action.dealt_cards)
        
        if all_action_cards != dealt_set:
            return ValidationResult(
                is_valid=False,
                error_message="Placed and discarded cards must match dealt cards"
            )
        
        # Check if cards are already placed or discarded
        for card in action.dealt_cards:
            if self._is_card_already_used(game_state, card):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Card {card} already used in game"
                )
        
        # Validate each placement position
        for card, position in action.placements:
            if not self._can_place_at_position(player, position):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Cannot place card at {position}"
                )
        
        return ValidationResult(is_valid=True)
    
    def validate_initial_placement(
        self,
        placement: InitialPlacement,
        player: Player,
        game_state: Game,
    ) -> ValidationResult:
        """
        Validate initial 5-card placement (Street 0).
        
        Checks:
        - Exactly 5 cards placed
        - No duplicate positions
        - Valid positions for each card
        """
        if len(placement.placements) != 5:
            return ValidationResult(
                is_valid=False,
                error_message=f"Must place 5 cards initially, got {len(placement.placements)}"
            )
        
        # Check positions
        positions = [pos for _, pos in placement.placements]
        if len(positions) != len(set(positions)):
            return ValidationResult(
                is_valid=False,
                error_message="Duplicate positions in placement"
            )
        
        # Validate each position
        for card, position in placement.placements:
            if not self._can_place_at_position(player, position):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Cannot place card at {position}"
                )
            
            if self._is_card_already_used(game_state, card):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Card {card} already used"
                )
        
        return ValidationResult(is_valid=True)
    
    def validate_fantasy_land_entry(
        self,
        player: Player,
        fantasy_state: FantasyLandState,
    ) -> ValidationResult:
        """
        Validate if player qualifies for Fantasy Land entry.
        
        Checks:
        - Player has complete layout
        - Top row meets QQ+ requirement
        - Not already in Fantasy Land
        """
        if fantasy_state.is_active:
            return ValidationResult(
                is_valid=False,
                error_message="Player already in Fantasy Land"
            )
        
        if not player.is_layout_complete():
            return ValidationResult(
                is_valid=False,
                error_message="Player layout not complete"
            )
        
        # Check top row qualification
        if self._fantasy_land_manager.check_entry_qualification(player.top_row):
            return ValidationResult(is_valid=True)
        
        return ValidationResult(
            is_valid=False,
            error_message="Top row does not qualify for Fantasy Land (need QQ+)"
        )
    
    def validate_fantasy_land_stay(
        self,
        player: Player,
        fantasy_state: FantasyLandState,
    ) -> ValidationResult:
        """
        Validate if player can stay in Fantasy Land.
        
        Checks:
        - Currently in Fantasy Land
        - Meets stay requirements
        """
        if not fantasy_state.is_active:
            return ValidationResult(
                is_valid=False,
                error_message="Player not in Fantasy Land"
            )
        
        if not player.is_layout_complete():
            return ValidationResult(
                is_valid=False,
                error_message="Player layout not complete"
            )
        
        # Check stay qualification
        if self._fantasy_land_manager.check_stay_qualification(
            player.top_row,
            player.middle_row,
            player.bottom_row
        ):
            return ValidationResult(is_valid=True)
        
        return ValidationResult(
            is_valid=False,
            error_message="Does not meet requirements to stay in Fantasy Land"
        )
    
    def validate_fantasy_land_placement(
        self,
        placed_cards: List[Card],
        dealt_cards: List[Card],
    ) -> ValidationResult:
        """
        Validate Fantasy Land card placement.
        
        Delegates to Fantasy Land manager for validation.
        """
        is_valid, error = self._fantasy_land_manager.validate_fantasy_placement(
            placed_cards,
            dealt_cards
        )
        
        return ValidationResult(
            is_valid=is_valid,
            error_message=error
        )
    
    def track_discarded_card(self, card: Card) -> None:
        """Track a discarded card."""
        self._discarded_cards.add(card)
    
    def _is_card_already_used(self, game: Game, card: Card) -> bool:
        """Check if card is already placed or discarded."""
        # Check placed cards
        if self._is_card_already_placed(game, card):
            return True
        
        # Check discarded cards
        if card in self._discarded_cards:
            return True
        
        return False
    
    def _can_place_at_position(self, player: Player, position: Position) -> bool:
        """Check if player can place a card at the given position."""
        if position.is_top_row:
            return len(player.top_row) < 3
        elif position.is_middle_row:
            return len(player.middle_row) < 5
        elif position.is_bottom_row:
            return len(player.bottom_row) < 5
        return False
    
    def get_discard_count(self) -> int:
        """Get total number of discarded cards."""
        return len(self._discarded_cards)
    
    def clear_discarded_cards(self) -> None:
        """Clear discarded cards tracking (for new game)."""
        self._discarded_cards.clear()