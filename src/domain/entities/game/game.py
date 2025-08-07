"""
Game Entity - Aggregate Root for OFC Game Management

The Game entity represents a complete OFC game session and serves as the
aggregate root for all game-related operations. It maintains game state,
enforces rules, and manages player interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from ...base import AggregateRoot
from ...events import CardPlacedEvent, GameCompletedEvent, RoundStartedEvent
from ...exceptions import GameStateError, InvalidCardPlacementError
from ...value_objects import Card, CardPosition, Deck, GameRules, Score
from .player import Player, PlayerId, PlayerStatus
from .position import Position

GameId = str


class GameStatus(Enum):
    """Game status enumeration."""
    
    WAITING = "waiting"      # Waiting for players to join
    IN_PROGRESS = "in_progress"  # Game is currently being played
    COMPLETED = "completed"  # Game finished normally
    PAUSED = "paused"       # Game temporarily paused
    CANCELLED = "cancelled"  # Game was cancelled


class Game(AggregateRoot):
    """
    Aggregate root for OFC game management.

    Encapsulates all game rules, state transitions, and business logic
    for Open Face Chinese Poker games.
    """

    def __init__(self, game_id: GameId, players: List[Player], rules: GameRules):
        super().__init__(game_id)

        # Validate initial state
        if len(players) < 2 or len(players) > 4:
            raise GameStateError("OFC games require 2-4 players")

        if len(set(p.id for p in players)) != len(players):
            raise GameStateError("All players must have unique IDs")

        # Initialize game state
        self._players: Dict[PlayerId, Player] = {p.id: p for p in players}
        self._rules = rules
        self._deck = Deck()
        self._current_round = 1
        self._current_player_index = 0
        self._completed_at: Optional[datetime] = None
        self._final_scores: Dict[PlayerId, Score] = {}

        # Deal initial cards based on rules
        self._deal_initial_cards()

        # Start first round
        self._start_round(1)

    @property
    def players(self) -> List[Player]:
        """Get all players in the game."""
        return list(self._players.values())

    @property
    def current_round(self) -> int:
        """Get current round number."""
        return self._current_round

    @property
    def rules(self) -> GameRules:
        """Get game rules."""
        return self._rules

    @property
    def is_completed(self) -> bool:
        """Check if game is completed."""
        return self._completed_at is not None

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get game completion timestamp."""
        return self._completed_at

    @property
    def final_scores(self) -> Dict[PlayerId, Score]:
        """Get final scores (only available after completion)."""
        return self._final_scores.copy()

    def get_current_player(self) -> Player:
        """Get the player whose turn it is."""
        if self.is_completed:
            raise GameStateError("Game is already completed")

        player_ids = list(self._players.keys())
        current_player_id = player_ids[self._current_player_index]
        return self._players[current_player_id]

    def place_card(
        self, player_id: PlayerId, card: Card, position: CardPosition
    ) -> None:
        """
        Place a card in player's layout with validation.

        Args:
            player_id: ID of the player placing the card
            card: Card to place
            position: Position where to place the card

        Raises:
            InvalidCardPlacementError: If placement violates rules
            GameStateError: If game state doesn't allow placement
        """
        if self.is_completed:
            raise GameStateError("Cannot place cards in completed game")

        # Validate it's the player's turn
        current_player = self.get_current_player()
        if player_id != current_player.id:
            raise GameStateError(f"It's not player {player_id}'s turn")

        # Validate player exists
        if player_id not in self._players:
            raise GameStateError(f"Player {player_id} not in game")

        player = self._players[player_id]

        # Card validation is handled by player entity
        # The player will check if they have the card

        # Validate placement is legal
        if not self._can_place_card(player, card, position):
            raise InvalidCardPlacementError(
                f"Cannot place {card} at {position} for player {player_id}"
            )

        # Apply placement
        player.place_card(card, position)
        # Card is already removed from deck during dealing
        self._increment_version()

        # Emit domain event
        self.add_domain_event(
            CardPlacedEvent(
                game_id=str(self.id),
                player_id=player_id,
                card=card,
                position=position,
                round_number=self._current_round,
            )
        )

        # Advance to next player
        self._advance_turn()

        # Check for round/game completion
        if self._is_round_complete():
            self._complete_round()

        if self._is_game_complete():
            self._complete_game()

    def get_analysis_position(self) -> Position:
        """Create position snapshot for strategy analysis."""
        return Position(
            game_id=str(self.id),
            players_hands={p.id: p.get_current_hand() for p in self.players},
            remaining_cards=self._deck.remaining_cards(),
            current_player_id=self.get_current_player().id,
            round_number=self._current_round,
            rules=self._rules,
        )

    def validate_layout(self, player_id: PlayerId) -> bool:
        """Validate player's current layout follows OFC rules."""
        if player_id not in self._players:
            return False

        player = self._players[player_id]
        return player.validate_layout()

    def calculate_scores(self) -> Dict[PlayerId, Score]:
        """Calculate current scores for all players."""
        # This would involve complex OFC scoring logic
        # For now, return placeholder
        return {player_id: Score(0, 0, 0) for player_id in self._players.keys()}

    def _deal_initial_cards(self) -> None:
        """Deal initial cards to all players."""
        from ...services import FantasyLandManager

        fantasy_manager = FantasyLandManager()

        for player in self.players:
            if player.is_in_fantasy_land:
                # Fantasy land players get all cards at once
                card_count = fantasy_manager.get_fantasy_land_card_count(
                    self._rules.variant
                )
                fantasy_cards = self._deck.deal_cards(card_count)
                player.receive_fantasy_land_cards(fantasy_cards)
            else:
                # Regular players get 5 cards initially
                initial_cards = self._deck.deal_cards(5)
                player.receive_initial_cards(initial_cards)

    def _start_round(self, round_number: int) -> None:
        """Start a new round."""
        current_player = self.get_current_player()

        self.add_domain_event(
            RoundStartedEvent(
                game_id=str(self.id),
                round_number=round_number,
                active_player_id=current_player.id,
            )
        )

    def _can_place_card(
        self, player: Player, card: Card, position: CardPosition
    ) -> bool:
        """Check if card placement is valid."""
        # Delegate to player for position-specific validation
        return player.can_place_card(card, position)

    def _advance_turn(self) -> None:
        """Advance to the next player's turn."""
        self._current_player_index = (self._current_player_index + 1) % len(
            self._players
        )

    def _is_round_complete(self) -> bool:
        """Check if current round is complete."""
        # Round is complete when all players have placed their cards
        return all(player.has_placed_card_this_round() for player in self.players)

    def _complete_round(self) -> None:
        """Complete the current round and prepare for next."""
        self._current_round += 1

        # Reset round state for all players
        for player in self.players:
            player.start_new_round()

        # Start next round if game not complete
        if not self._is_game_complete():
            self._start_round(self._current_round)

    def _is_game_complete(self) -> bool:
        """Check if game is complete."""
        # Game is complete when all players have 13 cards placed
        return all(player.is_layout_complete() for player in self.players)

    def _complete_game(self) -> None:
        """Complete the game and calculate final scores."""
        if self.is_completed:
            return

        # Check for fantasy land qualification before completing
        self._check_fantasy_land_qualification()

        self._completed_at = datetime.utcnow()
        self._final_scores = self.calculate_scores()

        # Determine winner
        winner_id = max(
            self._final_scores.keys(),
            key=lambda pid: self._final_scores[pid].total_points,
        )

        self.add_domain_event(
            GameCompletedEvent(
                game_id=str(self.id),
                final_scores=self._final_scores,
                winner_id=winner_id,
            )
        )

        self._increment_version()

    def _check_fantasy_land_qualification(self) -> None:
        """Check if any players qualify for fantasy land."""
        from ...services import FantasyLandManager, HandEvaluator

        fantasy_manager = FantasyLandManager()
        evaluator = HandEvaluator()

        for player in self.players:
            if player.is_layout_complete() and not player.status == PlayerStatus.FOULED:
                # Evaluate each row
                top_hand = evaluator.evaluate_hand(player.top_row)
                middle_hand = evaluator.evaluate_hand(player.middle_row)
                bottom_hand = evaluator.evaluate_hand(player.bottom_row)

                # Check qualification
                if fantasy_manager.qualifies_for_fantasy_land(
                    top_hand, middle_hand, bottom_hand
                ):
                    player.enter_fantasy_land()

                # If already in fantasy land, check if they can stay
                elif player.is_in_fantasy_land:
                    if fantasy_manager.can_stay_in_fantasy_land(
                        top_hand, middle_hand, bottom_hand
                    ):
                        # Player stays in fantasy land
                        pass
                    else:
                        player.exit_fantasy_land()

    def __repr__(self) -> str:
        """String representation of the game."""
        status = "completed" if self.is_completed else f"round {self._current_round}"
        return f"Game(id={self.id}, players={len(self.players)}, status={status})"
