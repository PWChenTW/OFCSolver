"""
Game Tree Node for OFC Solver

MVP implementation focusing on essential features only.
Following YAGNI principle - only what's needed for basic tree search.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from uuid import UUID

from ..base import ValueObject
from .card import Card
from .hand import Hand


@dataclass(frozen=True)
class GameTreeNode(ValueObject):
    """
    Represents a node in the OFC game tree.
    
    MVP version: Simple and memory-efficient.
    No complex optimizations, just the essentials.
    """
    
    # Node identification
    node_id: str  # Simple string ID for debugging
    depth: int    # How deep in the tree (0 = root)
    
    # Game state at this node
    player_hand: Hand  # Current hand state
    cards_placed: int  # Number of cards placed so far
    
    # For 3-pick-2 decisions
    dealt_cards: Optional[Tuple[Card, Card, Card]] = None
    possible_actions: Optional[List[Tuple[Card, Card]]] = None  # Pairs to place
    
    # Tree structure (using IDs to save memory)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    # Basic evaluation
    is_terminal: bool = False
    is_fouled: bool = False
    
    def __post_init__(self):
        """Validate node state."""
        if self.cards_placed < 0 or self.cards_placed > 13:
            raise ValueError(f"Invalid cards_placed: {self.cards_placed}")
            
        if self.depth < 0:
            raise ValueError(f"Invalid depth: {self.depth}")
            
        # Terminal nodes should have 13 cards (but during construction this might not be set correctly)
        # So we'll be lenient here for MVP
    
    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return len(self.children_ids) == 0
    
    @property
    def street(self) -> int:
        """Get current street (0-4 in Pineapple OFC)."""
        if self.cards_placed <= 5:
            return 0  # Initial placement
        return (self.cards_placed - 5) // 2 + 1
    
    def get_action_count(self) -> int:
        """Get number of possible actions from this node."""
        if self.possible_actions:
            return len(self.possible_actions)
        return 0


@dataclass(frozen=True) 
class NodeAction(ValueObject):
    """
    Represents an action taken at a node.
    
    MVP: Just track what cards were placed where.
    """
    
    from_node_id: str
    to_node_id: str
    cards_placed: Tuple[Card, Card]  # Which 2 cards were placed
    card_discarded: Card  # Which card was discarded
    
    # Optional metadata
    action_index: int = 0  # Which action (0-2 for 3-pick-2)
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"Place {self.cards_placed[0]} and {self.cards_placed[1]}, discard {self.card_discarded}"