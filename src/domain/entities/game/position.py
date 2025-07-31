"""
Position Entity for Game Analysis

The Position entity represents a snapshot of the game state at a specific
point in time, used for strategy analysis and solver calculations.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from ...base import DomainEntity
from ...value_objects import Card, Hand, GameRules
from .player import PlayerId


PositionId = str


class Position(DomainEntity):
    """
    Represents a game position for analysis.
    
    A position captures the complete state of an OFC game at a specific
    moment, including all player hands, remaining cards, and game context.
    This entity is used by the strategy engine for analysis.
    """
    
    def __init__(
        self, 
        game_id: str,
        players_hands: Dict[PlayerId, Hand],
        remaining_cards: List[Card],
        current_player_id: PlayerId,
        round_number: int,
        rules: GameRules,
        position_id: Optional[PositionId] = None
    ):
        # Generate position ID if not provided
        if position_id is None:
            position_id = self._generate_position_id(
                game_id, players_hands, remaining_cards, current_player_id, round_number
            )
        
        super().__init__(position_id)
        
        self._game_id = game_id
        self._players_hands = players_hands.copy()
        self._remaining_cards = remaining_cards.copy()
        self._current_player_id = current_player_id
        self._round_number = round_number
        self._rules = rules
        
        # Calculated properties (computed on demand)
        self._position_hash: Optional[str] = None
        self._complexity_score: Optional[float] = None
    
    @property
    def game_id(self) -> str:
        """Get the ID of the game this position belongs to."""
        return self._game_id
    
    @property
    def players_hands(self) -> Dict[PlayerId, Hand]:
        """Get copy of all player hands."""
        return self._players_hands.copy()
    
    @property
    def remaining_cards(self) -> List[Card]:
        """Get copy of remaining cards in deck."""
        return self._remaining_cards.copy()
    
    @property
    def current_player_id(self) -> PlayerId:
        """Get ID of player whose turn it is."""
        return self._current_player_id
    
    @property
    def round_number(self) -> int:
        """Get current round number."""
        return self._round_number
    
    @property
    def rules(self) -> GameRules:
        """Get game rules."""
        return self._rules
    
    @property
    def player_count(self) -> int:
        """Get number of players in position."""
        return len(self._players_hands)
    
    @property
    def cards_remaining_count(self) -> int:
        """Get number of cards remaining in deck."""
        return len(self._remaining_cards)
    
    def get_player_hand(self, player_id: PlayerId) -> Optional[Hand]:
        """Get hand for specific player."""
        return self._players_hands.get(player_id)
    
    def get_current_player_hand(self) -> Hand:
        """Get hand of current player."""
        hand = self._players_hands.get(self._current_player_id)
        if hand is None:
            raise ValueError(f"Current player {self._current_player_id} not found")
        return hand
    
    def get_opponent_hands(self) -> Dict[PlayerId, Hand]:
        """Get hands of all opponents (excluding current player)."""
        return {
            player_id: hand 
            for player_id, hand in self._players_hands.items()
            if player_id != self._current_player_id
        }
    
    def is_terminal_position(self) -> bool:
        """Check if this is a terminal (end-game) position."""
        # Position is terminal if all players have complete layouts
        return all(
            hand.is_complete() 
            for hand in self._players_hands.values()
        )
    
    def is_early_game(self) -> bool:
        """Check if this is an early game position."""
        return self._round_number <= 3
    
    def is_mid_game(self) -> bool:
        """Check if this is a mid game position."""
        return 4 <= self._round_number <= 8
    
    def is_end_game(self) -> bool:
        """Check if this is an end game position."""
        return self._round_number >= 9
    
    def get_position_hash(self) -> str:
        """
        Get unique hash for this position.
        
        Used for caching and position comparison. Two positions with
        the same hash are strategically equivalent.
        """
        if self._position_hash is None:
            self._position_hash = self._calculate_position_hash()
        return self._position_hash
    
    def get_complexity_score(self) -> float:
        """
        Get complexity score for this position.
        
        Higher scores indicate more complex positions that require
        more computational resources to analyze.
        """
        if self._complexity_score is None:
            self._complexity_score = self._calculate_complexity_score()
        return self._complexity_score
    
    def get_legal_moves(self) -> List['Move']:
        """Get all legal moves from this position."""
        current_hand = self.get_current_player_hand()
        legal_moves = []
        
        for card in current_hand.hand_cards:
            for position in current_hand.get_available_positions():
                from ...value_objects import Move  # Avoid circular import
                move = Move(card=card, position=position)
                legal_moves.append(move)
        
        return legal_moves
    
    def apply_move(self, move: 'Move') -> 'Position':
        """
        Create new position after applying a move.
        
        Args:
            move: Move to apply
            
        Returns:
            New Position after the move
        """
        # Create new hands dictionary
        new_hands = self._players_hands.copy()
        current_hand = new_hands[self._current_player_id]
        
        # Apply move to current player's hand
        new_current_hand = current_hand.place_card(move.card, move.position)
        new_hands[self._current_player_id] = new_current_hand
        
        # Remove card from remaining cards
        new_remaining = [c for c in self._remaining_cards if c != move.card]
        
        # Determine next player
        player_ids = list(self._players_hands.keys())
        current_index = player_ids.index(self._current_player_id)
        next_player_id = player_ids[(current_index + 1) % len(player_ids)]
        
        # Create new position
        return Position(
            game_id=self._game_id,
            players_hands=new_hands,
            remaining_cards=new_remaining,
            current_player_id=next_player_id,
            round_number=self._round_number,
            rules=self._rules
        )
    
    def to_analysis_format(self) -> Dict:
        """Convert position to format suitable for analysis engines."""
        return {
            'position_id': str(self.id),
            'game_id': self._game_id,
            'round_number': self._round_number,
            'current_player': self._current_player_id,
            'players_hands': {
                pid: hand.to_dict() 
                for pid, hand in self._players_hands.items()
            },
            'remaining_cards': [str(card) for card in self._remaining_cards],
            'rules': self._rules.to_dict(),
            'position_hash': self.get_position_hash(),
            'complexity_score': self.get_complexity_score()
        }
    
    def _generate_position_id(
        self, 
        game_id: str,
        players_hands: Dict[PlayerId, Hand],
        remaining_cards: List[Card],
        current_player_id: PlayerId,
        round_number: int
    ) -> PositionId:
        """Generate unique position ID."""
        import hashlib
        
        # Create deterministic string representation
        position_data = f"{game_id}:{round_number}:{current_player_id}:"
        position_data += ":".join(sorted([
            f"{pid}:{hand.to_string()}" 
            for pid, hand in players_hands.items()
        ]))
        position_data += ":" + ":".join(sorted(str(card) for card in remaining_cards))
        
        # Generate hash-based ID
        hash_digest = hashlib.md5(position_data.encode()).hexdigest()
        return f"pos_{hash_digest[:16]}"
    
    def _calculate_position_hash(self) -> str:
        """Calculate deterministic hash for position caching."""
        import hashlib
        
        # Normalize position data for consistent hashing
        normalized_data = {
            'hands': {
                pid: hand.normalize_for_comparison() 
                for pid, hand in self._players_hands.items()
            },
            'remaining_cards': sorted(str(card) for card in self._remaining_cards),
            'current_player': self._current_player_id,
            'round': self._round_number
        }
        
        # Create hash
        data_str = str(sorted(normalized_data.items()))
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _calculate_complexity_score(self) -> float:
        """Calculate position complexity for analysis prioritization."""
        base_score = 1.0
        
        # Factor in remaining cards (more cards = more complex)
        cards_factor = len(self._remaining_cards) / 52.0
        
        # Factor in game phase (mid-game is most complex)
        if self.is_early_game():
            phase_factor = 0.5
        elif self.is_mid_game():
            phase_factor = 1.0
        else:  # end_game
            phase_factor = 0.3
        
        # Factor in number of legal moves
        legal_moves_count = len(self.get_legal_moves())
        moves_factor = min(legal_moves_count / 15.0, 1.0)  # Cap at 15 moves
        
        # Factor in incomplete hands (more flexibility = more complex)
        incomplete_hands = sum(
            1 for hand in self._players_hands.values() 
            if not hand.is_complete()
        )
        hands_factor = incomplete_hands / len(self._players_hands)
        
        # Combine factors
        complexity = base_score * cards_factor * phase_factor * moves_factor * hands_factor
        
        return round(complexity * 100, 2)  # Scale to 0-100 range
    
    def __eq__(self, other) -> bool:
        """Positions are equal if they have the same hash."""
        if not isinstance(other, Position):
            return False
        return self.get_position_hash() == other.get_position_hash()
    
    def __hash__(self) -> int:
        """Hash based on position hash."""
        return hash(self.get_position_hash())
    
    def __repr__(self) -> str:
        """String representation of position."""
        return (f"Position(id={self.id}, game={self._game_id}, "
                f"round={self._round_number}, player={self._current_player_id}, "
                f"complexity={self.get_complexity_score():.1f})")