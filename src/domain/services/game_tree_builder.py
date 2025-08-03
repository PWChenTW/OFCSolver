"""
Game Tree Builder for OFC Solver System.

MVP implementation focusing on basic tree building for Pineapple OFC.
Following YAGNI principle - only essential features for now.
"""

from typing import Dict, List, Optional, Tuple
from itertools import combinations
import uuid

from ..base import DomainService
from ..value_objects import Card
from ..value_objects.game_tree_node import GameTreeNode, NodeAction
from ..value_objects.hand import Hand
from ..value_objects.card_position import CardPosition
from .pineapple_evaluator import PineappleHandEvaluator
from .tree_traversal import TreeTraversal
from .tree_pruning import TreePruning
from .transposition_table import TranspositionTable, PositionKey


class GameTreeBuilder(DomainService):
    """
    Builds game decision trees for Pineapple OFC positions.

    MVP version: Simple tree building without complex optimizations.
    Focus on correctness over performance for initial implementation.
    """

    def __init__(self, evaluator: Optional[PineappleHandEvaluator] = None):
        """Initialize with hand evaluator."""
        self.evaluator = evaluator or PineappleHandEvaluator()
        self.nodes: Dict[str, GameTreeNode] = {}  # Node storage
        self.actions: Dict[str, NodeAction] = {}  # Action storage
        self._node_counter = 0

        # Additional services
        self.traversal = TreeTraversal(self.nodes, self.actions)
        self.pruning = TreePruning(self.nodes, self.actions, self.traversal)
        self.transposition = TranspositionTable()

    def build_tree_from_position(
        self,
        current_hand: Hand,
        remaining_deck: List[Card],
        max_depth: int = 2,  # Default shallow for MVP
    ) -> GameTreeNode:
        """
        Build a game tree from current position.

        MVP approach:
        - Limited depth to avoid memory issues
        - No transposition table yet
        - Simple breadth-first construction

        Args:
            current_hand: Current hand state
            remaining_deck: Cards left in deck
            max_depth: How many streets to look ahead

        Returns:
            Root node of the tree
        """
        # Create root node
        root_id = self._generate_node_id()
        root = GameTreeNode(
            node_id=root_id,
            depth=0,
            player_hand=current_hand,
            cards_placed=len(current_hand.get_all_placed_cards()),
            is_terminal=(len(current_hand.get_all_placed_cards()) >= 13),
        )

        self.nodes[root_id] = root

        # Build tree if not terminal and depth allows
        if not root.is_terminal and max_depth > 0:
            self._expand_node(root, remaining_deck, max_depth)

        return root

    def _expand_node(
        self, node: GameTreeNode, remaining_deck: List[Card], remaining_depth: int
    ) -> None:
        """
        Expand a node by generating all possible actions.

        MVP: Simple expansion without pruning.
        """
        if remaining_depth <= 0 or node.is_terminal:
            return

        # For Pineapple OFC: deal 3 cards, place 2
        if len(remaining_deck) < 3:
            return  # Not enough cards

        # Simple approach: just take next 3 cards
        # (In real game, this would be random)
        dealt_cards = tuple(remaining_deck[:3])

        # Generate all possible 2-card placements
        possible_placements = list(combinations(dealt_cards, 2))

        # Update node with dealt cards info (create new immutable node)
        updated_node = GameTreeNode(
            node_id=node.node_id,
            depth=node.depth,
            player_hand=node.player_hand,
            cards_placed=node.cards_placed,
            dealt_cards=dealt_cards,
            possible_actions=possible_placements,
            parent_id=node.parent_id,
            children_ids=[],  # Will be updated as we create children
            is_terminal=node.is_terminal,
            is_fouled=node.is_fouled,
        )
        self.nodes[node.node_id] = updated_node

        children_ids = []  # Track children we create

        # Create child nodes for each possible action
        for i, (card1, card2) in enumerate(possible_placements):
            # Determine which card is discarded
            discarded = [c for c in dealt_cards if c not in (card1, card2)][0]

            # Try to place cards (simplified for MVP)
            child_hand = self._try_place_cards(node.player_hand, [card1, card2])

            if child_hand is None:
                continue  # Invalid placement

            # Check for transposition (if enabled)
            if self.transposition:
                position_key = PositionKey.from_hand(child_hand, node.cards_placed + 2)
                existing_node_id = self.transposition.lookup(position_key)

                if existing_node_id and existing_node_id in self.nodes:
                    # Position already exists, just link to it
                    child_id = existing_node_id
                    children_ids.append(child_id)

                    # Still create action for this path
                    action = NodeAction(
                        from_node_id=node.node_id,
                        to_node_id=child_id,
                        cards_placed=(card1, card2),
                        card_discarded=discarded,
                        action_index=i,
                    )
                    self.actions[f"{node.node_id}->{child_id}"] = action
                    continue

            # Create new child node
            child_id = self._generate_node_id()
            child = GameTreeNode(
                node_id=child_id,
                depth=node.depth + 1,
                player_hand=child_hand,
                cards_placed=node.cards_placed + 2,
                parent_id=node.node_id,
                is_terminal=(node.cards_placed + 2 >= 13),
                is_fouled=self._check_fouled(child_hand),
            )

            # Store in transposition table (if enabled)
            if self.transposition:
                position_key = PositionKey.from_hand(child_hand, node.cards_placed + 2)
                self.transposition.store(position_key, child_id)

            # Create action
            action = NodeAction(
                from_node_id=node.node_id,
                to_node_id=child_id,
                cards_placed=(card1, card2),
                card_discarded=discarded,
                action_index=i,
            )

            # Store node and action
            self.nodes[child_id] = child
            self.actions[f"{node.node_id}->{child_id}"] = action

            # Track this child
            children_ids.append(child_id)

            # Recursively expand child
            new_deck = remaining_deck[3:]  # Remove dealt cards
            self._expand_node(child, new_deck, remaining_depth - 1)

        # After all children created, update parent node with children IDs
        final_node = GameTreeNode(
            node_id=node.node_id,
            depth=node.depth,
            player_hand=node.player_hand,
            cards_placed=node.cards_placed,
            dealt_cards=dealt_cards,
            possible_actions=possible_placements,
            parent_id=node.parent_id,
            children_ids=children_ids,
            is_terminal=node.is_terminal,
            is_fouled=node.is_fouled,
        )
        self.nodes[node.node_id] = final_node

    def _try_place_cards(self, hand: Hand, cards: List[Card]) -> Optional[Hand]:
        """
        Try to place cards in available positions.

        MVP: Try all possible position combinations for the 2 cards.
        """
        # Get available positions
        available_positions = []
        if len(hand.top_row) < 3:
            available_positions.extend([CardPosition.TOP] * (3 - len(hand.top_row)))
        if len(hand.middle_row) < 5:
            available_positions.extend(
                [CardPosition.MIDDLE] * (5 - len(hand.middle_row))
            )
        if len(hand.bottom_row) < 5:
            available_positions.extend(
                [CardPosition.BOTTOM] * (5 - len(hand.bottom_row))
            )

        # Need at least 2 positions for 2 cards
        if len(available_positions) < 2:
            return None

        # First, add cards to hand_cards (they need to be available to place)
        # This is a bit hacky for MVP but works
        new_hand = Hand.from_layout(
            top=list(hand.top_row),
            middle=list(hand.middle_row),
            bottom=list(hand.bottom_row),
            hand=list(cards),  # Add the cards to be placed
        )

        # For MVP, just try first available positions
        # (In real solver, we'd try all combinations)
        position_idx = 0

        for card in cards:
            if position_idx >= len(available_positions):
                return None

            position = available_positions[position_idx]
            try:
                new_hand = new_hand.place_card(card, position)
                position_idx += 1
            except Exception as e:
                print(f"DEBUG: Exception placing {card} at {position}: {e}")
                return None

        return new_hand

    def _check_fouled(self, hand: Hand) -> bool:
        """
        Check if hand is fouled.

        MVP: Simple check - just validate row strengths.
        """
        if not hand.is_complete:
            return False

        # Need complete rows to evaluate (3 for top, 5 for middle/bottom)
        if (
            len(hand.top_row) != 3
            or len(hand.middle_row) != 5
            or len(hand.bottom_row) != 5
        ):
            return False  # Can't be fouled if not complete

        # Evaluate each row
        top_rank = self.evaluator.evaluate_hand(hand.top_row)
        middle_rank = self.evaluator.evaluate_hand(hand.middle_row)
        bottom_rank = self.evaluator.evaluate_hand(hand.bottom_row)

        # Check strength progression: bottom >= middle >= top
        if bottom_rank.hand_type.value < middle_rank.hand_type.value:
            return True
        if middle_rank.hand_type.value < top_rank.hand_type.value:
            return True

        # For same hand types, check strength values
        if bottom_rank.hand_type == middle_rank.hand_type:
            if bottom_rank.strength_value < middle_rank.strength_value:
                return True
        if middle_rank.hand_type == top_rank.hand_type:
            if middle_rank.strength_value < top_rank.strength_value:
                return True

        return False

    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        self._node_counter += 1
        return f"node_{self._node_counter}"

    def get_tree_stats(self, root: GameTreeNode) -> Dict[str, int]:
        """
        Get basic statistics about the tree.

        MVP: Simple stats for debugging.
        """
        total_nodes = len(self.nodes)
        leaf_nodes = sum(1 for n in self.nodes.values() if n.is_leaf)
        terminal_nodes = sum(1 for n in self.nodes.values() if n.is_terminal)
        fouled_nodes = sum(1 for n in self.nodes.values() if n.is_fouled)

        max_depth = max((n.depth for n in self.nodes.values()), default=0)

        return {
            "total_nodes": total_nodes,
            "leaf_nodes": leaf_nodes,
            "terminal_nodes": terminal_nodes,
            "fouled_nodes": fouled_nodes,
            "max_depth": max_depth,
            "total_actions": len(self.actions),
        }
