"""
Player Entity for OFC Game Management

The Player entity represents an individual player within an OFC game.
It manages the player's card layout, hand state, and placement rules.
"""

from enum import Enum
from typing import List

from ...base import DomainEntity
from ...exceptions import GameStateError, InvalidCardPlacementError
from ...value_objects import Card, CardPosition, Hand

PlayerId = str


class PlayerStatus(Enum):
    """Player status within a game."""

    ACTIVE = "active"
    FOULED = "fouled"  # Invalid layout
    FANTASY_LAND = "fantasy_land"
    ELIMINATED = "eliminated"


class Player(DomainEntity):
    """
    Represents a player in an OFC game.

    Manages the player's three-row layout (top, middle, bottom),
    card placement rules, and game state.
    """

    def __init__(self, player_id: PlayerId, name: str):
        super().__init__(player_id)
        self._name = name
        self._status = PlayerStatus.ACTIVE

        # Three-row layout for OFC
        self._top_row: List[Card] = []  # 3 cards max
        self._middle_row: List[Card] = []  # 5 cards max
        self._bottom_row: List[Card] = []  # 5 cards max

        # Cards in hand (not yet placed)
        self._hand_cards: List[Card] = []

        # Track if player has placed card this round
        self._placed_card_this_round = False

        # Fantasy land state
        self._in_fantasy_land = False
        self._fantasy_land_cards: List[Card] = []

    @property
    def name(self) -> str:
        """Get player name."""
        return self._name

    @property
    def status(self) -> PlayerStatus:
        """Get player status."""
        return self._status

    @property
    def top_row(self) -> List[Card]:
        """Get top row cards."""
        return self._top_row.copy()

    @property
    def middle_row(self) -> List[Card]:
        """Get middle row cards."""
        return self._middle_row.copy()

    @property
    def bottom_row(self) -> List[Card]:
        """Get bottom row cards."""
        return self._bottom_row.copy()

    @property
    def hand_cards(self) -> List[Card]:
        """Get cards currently in hand."""
        return self._hand_cards.copy()

    @property
    def is_in_fantasy_land(self) -> bool:
        """Check if player is in fantasy land."""
        return self._in_fantasy_land

    @property
    def total_cards_placed(self) -> int:
        """Get total number of cards placed in layout."""
        return len(self._top_row) + len(self._middle_row) + len(self._bottom_row)

    def receive_initial_cards(self, cards: List[Card]) -> None:
        """Receive initial dealing of cards."""
        if len(self._hand_cards) > 0:
            raise GameStateError("Player already has cards")

        if len(cards) != 5:
            raise GameStateError("Initial deal must be exactly 5 cards")

        self._hand_cards = cards.copy()
        self._increment_version()

    def receive_card(self, card: Card) -> None:
        """Receive a new card to hand."""
        if self._in_fantasy_land:
            self._fantasy_land_cards.append(card)
        else:
            self._hand_cards.append(card)
        self._increment_version()

    def can_place_card(self, card: Card, position: CardPosition) -> bool:
        """
        Check if card can be placed at the specified position.

        Args:
            card: Card to place
            position: Position to place card

        Returns:
            True if placement is valid, False otherwise
        """
        # Check if player has the card
        if card not in self._hand_cards:
            return False

        # Check position availability
        if position == CardPosition.TOP:
            return len(self._top_row) < 3
        elif position == CardPosition.MIDDLE:
            return len(self._middle_row) < 5
        elif position == CardPosition.BOTTOM:
            return len(self._bottom_row) < 5

        return False

    def place_card(self, card: Card, position: CardPosition) -> None:
        """
        Place a card at the specified position.

        Args:
            card: Card to place
            position: Position to place card

        Raises:
            InvalidCardPlacementError: If placement is invalid
        """
        if not self.can_place_card(card, position):
            raise InvalidCardPlacementError(f"Cannot place {card} at {position}")

        # Remove card from hand
        self._hand_cards.remove(card)

        # Place card in appropriate row
        if position == CardPosition.TOP:
            self._top_row.append(card)
        elif position == CardPosition.MIDDLE:
            self._middle_row.append(card)
        elif position == CardPosition.BOTTOM:
            self._bottom_row.append(card)

        self._placed_card_this_round = True
        self._increment_version()

        # Check for fouling after placement
        if self.is_layout_complete() and not self.validate_layout():
            self._status = PlayerStatus.FOULED

    def validate_layout(self) -> bool:
        """
        Validate current layout follows OFC rules.

        In OFC, bottom row must be stronger than middle row,
        and middle row must be stronger than top row.

        Returns:
            True if layout is valid, False if fouled
        """
        # Need at least some cards to validate
        if self.total_cards_placed == 0:
            return True

        # If layout is complete, check strength progression
        if self.is_layout_complete():
            from ...services import HandEvaluator  # Avoid circular import

            evaluator = HandEvaluator()

            # Evaluate each row
            top_hand = evaluator.evaluate_hand(self._top_row)
            middle_hand = evaluator.evaluate_hand(self._middle_row)
            bottom_hand = evaluator.evaluate_hand(self._bottom_row)

            # Check strength progression (higher values = stronger hands)
            if bottom_hand.strength_value <= middle_hand.strength_value:
                return False
            if middle_hand.strength_value <= top_hand.strength_value:
                return False

        return True

    def is_layout_complete(self) -> bool:
        """Check if player has placed all 13 cards."""
        return self.total_cards_placed == 13

    def has_placed_card_this_round(self) -> bool:
        """Check if player has placed a card this round."""
        return self._placed_card_this_round

    def start_new_round(self) -> None:
        """Start a new round (reset round state)."""
        self._placed_card_this_round = False

    def get_current_hand(self) -> Hand:
        """Get current hand representation for analysis."""
        return Hand(
            top_row=self._top_row.copy(),
            middle_row=self._middle_row.copy(),
            bottom_row=self._bottom_row.copy(),
            hand_cards=self._hand_cards.copy(),
        )

    def calculate_royalties(self) -> int:
        """Calculate royalty bonuses for current layout."""
        if not self.is_layout_complete():
            return 0

        from ...services import RoyaltyCalculator  # Avoid circular import

        calculator = RoyaltyCalculator()

        return calculator.calculate_total_royalties(
            top_row=self._top_row,
            middle_row=self._middle_row,
            bottom_row=self._bottom_row,
        )

    def enter_fantasy_land(self) -> None:
        """Enter fantasy land mode."""
        self._in_fantasy_land = True
        self._status = PlayerStatus.FANTASY_LAND
        self._increment_version()

    def exit_fantasy_land(self) -> None:
        """Exit fantasy land mode."""
        self._in_fantasy_land = False
        self._status = PlayerStatus.ACTIVE
        self._fantasy_land_cards.clear()
        self._increment_version()

    def get_available_positions(self) -> List[CardPosition]:
        """Get list of positions where cards can still be placed."""
        positions = []

        if len(self._top_row) < 3:
            positions.append(CardPosition.TOP)
        if len(self._middle_row) < 5:
            positions.append(CardPosition.MIDDLE)
        if len(self._bottom_row) < 5:
            positions.append(CardPosition.BOTTOM)

        return positions

    def get_row_cards(self, position: CardPosition) -> List[Card]:
        """Get cards in specific row."""
        if position == CardPosition.TOP:
            return self._top_row.copy()
        elif position == CardPosition.MIDDLE:
            return self._middle_row.copy()
        elif position == CardPosition.BOTTOM:
            return self._bottom_row.copy()
        else:
            return []

    def __repr__(self) -> str:
        """String representation of the player."""
        return (
            f"Player(id={self.id}, name='{self._name}', "
            f"cards_placed={self.total_cards_placed}, status={self._status.value})"
        )
