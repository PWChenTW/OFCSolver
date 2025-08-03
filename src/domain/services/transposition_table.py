"""
Transposition Table for Game Tree

MVP implementation to handle duplicate positions.
Helps reduce tree size by recognizing equivalent game states.
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

from ..base import DomainService
from ..value_objects import Card, Hand
from ..value_objects.game_tree_node import GameTreeNode


@dataclass(frozen=True)
class PositionKey:
    """
    Represents a unique position for transposition detection.

    MVP: Simple key based on cards in each row.
    """

    top_cards: Tuple[str, ...]  # Sorted card strings
    middle_cards: Tuple[str, ...]
    bottom_cards: Tuple[str, ...]
    cards_placed: int

    @staticmethod
    def from_hand(hand: Hand, cards_placed: int) -> "PositionKey":
        """Create position key from hand."""
        # Sort cards in each row for consistent keys
        top = tuple(sorted(str(c) for c in hand.top_row))
        middle = tuple(sorted(str(c) for c in hand.middle_row))
        bottom = tuple(sorted(str(c) for c in hand.bottom_row))

        return PositionKey(
            top_cards=top,
            middle_cards=middle,
            bottom_cards=bottom,
            cards_placed=cards_placed,
        )


class TranspositionTable(DomainService):
    """
    Manages transposition detection and lookup.

    MVP version: Simple in-memory table with basic operations.
    """

    def __init__(self):
        """Initialize empty transposition table."""
        self.table: Dict[PositionKey, str] = {}  # Maps position to node_id
        self.hit_count = 0
        self.miss_count = 0

    def lookup(self, position_key: PositionKey) -> Optional[str]:
        """
        Look up a position in the table.

        Args:
            position_key: Position to look up

        Returns:
            Node ID if found, None otherwise
        """
        node_id = self.table.get(position_key)
        if node_id:
            self.hit_count += 1
        else:
            self.miss_count += 1
        return node_id

    def store(self, position_key: PositionKey, node_id: str) -> None:
        """
        Store a position in the table.

        Args:
            position_key: Position key
            node_id: Node ID for this position
        """
        self.table[position_key] = node_id

    def check_and_store(self, node: GameTreeNode) -> Tuple[bool, Optional[str]]:
        """
        Check if position exists and store if not.

        Args:
            node: Game tree node

        Returns:
            (exists, existing_node_id)
        """
        position_key = PositionKey.from_hand(node.player_hand, node.cards_placed)

        existing_id = self.lookup(position_key)
        if existing_id:
            return True, existing_id
        else:
            self.store(position_key, node.node_id)
            return False, None

    def clear(self) -> None:
        """Clear the transposition table."""
        self.table.clear()
        self.hit_count = 0
        self.miss_count = 0

    def size(self) -> int:
        """Get number of positions stored."""
        return len(self.table)

    def hit_rate(self) -> float:
        """Calculate hit rate."""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return self.hit_count / total

    def get_statistics(self) -> Dict[str, int]:
        """Get table statistics."""
        return {
            "size": self.size(),
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate": round(self.hit_rate() * 100, 2),
        }

    def find_equivalent_nodes(self, nodes: Dict[str, GameTreeNode]) -> List[List[str]]:
        """
        Find groups of equivalent nodes.

        Args:
            nodes: All nodes in tree

        Returns:
            List of equivalent node groups
        """
        position_groups: Dict[PositionKey, List[str]] = {}

        for node_id, node in nodes.items():
            key = PositionKey.from_hand(node.player_hand, node.cards_placed)
            if key not in position_groups:
                position_groups[key] = []
            position_groups[key].append(node_id)

        # Return only groups with duplicates
        return [group for group in position_groups.values() if len(group) > 1]
