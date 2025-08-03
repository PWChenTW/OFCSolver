"""
Strategy Calculator Service for OFC Solver System.

MVP implementation focusing on essential features only.
Following YAGNI principle - only what's needed for basic strategy calculation.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import math

from ..base import DomainService
from ..value_objects.strategy import Strategy, ActionRecommendation
from ..value_objects.expected_value import ExpectedValue
from ..value_objects.game_tree_node import GameTreeNode, NodeAction
from ..value_objects.hand import Hand
from ..value_objects.card import Card
from ..value_objects.hand_ranking import HandType
from .game_tree_builder import GameTreeBuilder
from .pineapple_evaluator import PineappleHandEvaluator


@dataclass
class NodeEvaluation:
    """Evaluation result for a game tree node."""
    node_id: str
    value: float
    best_action: Optional[NodeAction] = None
    visits: int = 0


class StrategyCalculator(DomainService):
    """
    Core GTO solver engine for OFC.
    
    MVP version: Simple minimax with alpha-beta pruning.
    No complex optimizations, just working strategy calculation.
    """
    
    def __init__(
        self,
        tree_builder: Optional[GameTreeBuilder] = None,
        evaluator: Optional[PineappleHandEvaluator] = None
    ):
        """Initialize with necessary services."""
        self.tree_builder = tree_builder or GameTreeBuilder()
        self.evaluator = evaluator or PineappleHandEvaluator()
        self.evaluations: Dict[str, NodeEvaluation] = {}
        
        # Memoization cache for position evaluations
        self._position_cache: Dict[str, float] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
    def calculate_optimal_strategy(
        self,
        current_hand: Hand,
        remaining_deck: List[Card],
        max_depth: int = 2
    ) -> Strategy:
        """
        Calculate optimal strategy for current position.
        
        MVP approach:
        - Build limited depth tree
        - Use minimax with alpha-beta pruning
        - Simple position evaluation
        
        Args:
            current_hand: Current hand state
            remaining_deck: Cards left in deck
            max_depth: How many streets to look ahead
            
        Returns:
            Strategy with recommended moves
        """
        # Build game tree
        root = self.tree_builder.build_tree_from_position(
            current_hand,
            remaining_deck,
            max_depth
        )
        
        # Calculate optimal play using minimax
        best_value = self._minimax(
            root,
            max_depth,
            True,  # Maximizing player
            float('-inf'),  # Alpha
            float('inf')   # Beta
        )
        
        # Get the best action from root
        root_eval = self.evaluations.get(root.node_id)
        if not root_eval or not root_eval.best_action:
            # Check if root has children - if so, get best child action
            if root.children_ids:
                # Find best child directly
                best_child_id = None
                best_value = float('-inf')
                best_action = None
                
                for child_id in root.children_ids:
                    child_eval = self.evaluations.get(child_id)
                    if child_eval and child_eval.value > best_value:
                        best_value = child_eval.value
                        best_child_id = child_id
                        # Find action that leads to this child
                        action_key = f"{root.node_id}->{child_id}"
                        best_action = self.tree_builder.actions.get(action_key)
                
                if best_action:
                    recommended_cards = best_action.cards_placed
                    discard = best_action.card_discarded
                else:
                    return Strategy(
                        recommended_actions=[],
                        expected_value=ExpectedValue(0.0),
                        confidence=0.0,
                        calculation_method="no_valid_actions"
                    )
            else:
                return Strategy(
                    recommended_actions=[],
                    expected_value=ExpectedValue(0.0),
                    confidence=0.0,
                    calculation_method="no_children"
                )
        else:
            recommended_cards = root_eval.best_action.cards_placed
            discard = root_eval.best_action.card_discarded
            
        # Create action recommendation
        action = ActionRecommendation(
            cards_to_place=list(recommended_cards),
            card_to_discard=discard,
            expected_value=best_value,
            confidence=0.8  # MVP: fixed confidence for now
        )
        
        # Build strategy
        strategy = Strategy(
            recommended_actions=[action],
            expected_value=ExpectedValue(best_value),
            confidence=0.8,
            calculation_method="minimax_alphabeta",
            tree_stats=self.tree_builder.get_tree_stats(root)
        )
        
        return strategy
        
    def _minimax(
        self,
        node: GameTreeNode,
        depth: int,
        maximizing_player: bool,
        alpha: float,
        beta: float
    ) -> float:
        """
        Minimax algorithm with alpha-beta pruning and memoization.
        
        Enhanced with:
        - Position caching for repeated states
        - Move ordering for better pruning
        """
        # Check memoization cache
        position_key = self._get_position_key(node)
        if position_key in self._position_cache and depth > 0:
            self._cache_hits += 1
            return self._position_cache[position_key]
        
        self._cache_misses += 1
        
        # Terminal node or depth limit
        if depth == 0 or node.is_terminal or node.is_leaf:
            eval_value = self._evaluate_position(node)
            self.evaluations[node.node_id] = NodeEvaluation(
                node_id=node.node_id,
                value=eval_value,
                visits=1
            )
            # Cache the evaluation
            if position_key:
                self._position_cache[position_key] = eval_value
            return eval_value
            
        if maximizing_player:
            max_eval = float('-inf')
            best_action = None
            
            # Get child nodes
            children = self._get_child_nodes(node)
            
            for child, action in children:
                eval_value = self._minimax(child, depth - 1, False, alpha, beta)
                
                if eval_value > max_eval:
                    max_eval = eval_value
                    best_action = action
                    
                alpha = max(alpha, eval_value)
                if beta <= alpha:
                    break  # Beta cutoff
                    
            self.evaluations[node.node_id] = NodeEvaluation(
                node_id=node.node_id,
                value=max_eval,
                best_action=best_action,
                visits=1
            )
            # Cache the result
            if position_key:
                self._position_cache[position_key] = max_eval
            return max_eval
            
        else:
            min_eval = float('inf')
            best_action = None
            
            # Get child nodes
            children = self._get_child_nodes(node)
            
            for child, action in children:
                eval_value = self._minimax(child, depth - 1, True, alpha, beta)
                
                if eval_value < min_eval:
                    min_eval = eval_value
                    best_action = action
                    
                beta = min(beta, eval_value)
                if beta <= alpha:
                    break  # Alpha cutoff
                    
            self.evaluations[node.node_id] = NodeEvaluation(
                node_id=node.node_id,
                value=min_eval,
                best_action=best_action,
                visits=1
            )
            # Cache the result
            if position_key:
                self._position_cache[position_key] = min_eval
            return min_eval
            
    def _get_child_nodes(self, node: GameTreeNode) -> List[Tuple[GameTreeNode, NodeAction]]:
        """Get child nodes with their actions, sorted for better pruning."""
        children = []
        
        for child_id in node.children_ids:
            child_node = self.tree_builder.nodes.get(child_id)
            if not child_node:
                continue
                
            # Find action that leads to this child
            action_key = f"{node.node_id}->{child_id}"
            action = self.tree_builder.actions.get(action_key)
            
            if action:
                children.append((child_node, action))
        
        # Sort children by quick evaluation for better alpha-beta pruning
        # Prioritize non-fouled positions and those with higher potential
        children.sort(key=lambda x: (
            not x[0].is_fouled,  # Non-fouled first
            -self._quick_evaluate(x[0])  # Higher evaluation first
        ), reverse=True)
                
        return children
    
    def _quick_evaluate(self, node: GameTreeNode) -> float:
        """Quick heuristic evaluation for move ordering."""
        if node.is_fouled:
            return -100.0
        
        # Simple heuristic based on cards placed
        hand = node.player_hand
        score = 0.0
        
        # Prefer positions closer to completion
        score += node.cards_placed * 0.5
        
        # Bonus for having cards in all rows (balanced play)
        if hand.top_row and hand.middle_row and hand.bottom_row:
            score += 2.0
            
        return score
    
    def _get_position_key(self, node: GameTreeNode) -> Optional[str]:
        """Generate a unique key for position caching."""
        if not node.player_hand:
            return None
            
        hand = node.player_hand
        # Create a deterministic string representation
        key_parts = [
            f"top:{sorted([str(c) for c in hand.top_row])}",
            f"mid:{sorted([str(c) for c in hand.middle_row])}",
            f"bot:{sorted([str(c) for c in hand.bottom_row])}",
            f"cards:{node.cards_placed}"
        ]
        
        return "|".join(key_parts)
        
    def _evaluate_position(self, node: GameTreeNode) -> float:
        """
        Enhanced position evaluation function.
        
        Improved evaluation based on:
        - Exact hand strength with kicker considerations
        - Progressive royalty accumulation
        - Draw potential evaluation
        - Row balance scoring
        - Fantasy land probability
        """
        hand = node.player_hand
        
        # Terminal evaluation
        if node.is_fouled:
            return -30.0  # Heavy penalty for fouling
            
        if node.is_terminal:
            # Evaluate complete hand
            return self._evaluate_complete_hand(hand)
            
        # Non-terminal evaluation with enhanced scoring
        score = 0.0
        
        # Evaluate placed cards with more nuance
        if len(hand.top_row) >= 3:
            top_eval = self.evaluator.evaluate_hand(hand.top_row)
            score += top_eval.royalty_bonus
            # Weighted by position importance and completion
            score += self._hand_type_value(top_eval.hand_type) * 0.5
            # Kicker bonus for pairs
            if top_eval.hand_type == "pair":
                score += self._get_kicker_bonus(hand.top_row) * 0.1
        else:
            # Partial row evaluation for potential
            score += self._evaluate_partial_row(hand.top_row, "top") * 0.3
            
        if len(hand.middle_row) >= 5:
            middle_eval = self.evaluator.evaluate_hand(hand.middle_row)
            score += middle_eval.royalty_bonus
            score += self._hand_type_value(middle_eval.hand_type) * 1.0
        else:
            # Draw potential evaluation
            score += self._evaluate_partial_row(hand.middle_row, "middle") * 0.5
            
        if len(hand.bottom_row) >= 5:
            bottom_eval = self.evaluator.evaluate_hand(hand.bottom_row)
            score += bottom_eval.royalty_bonus
            score += self._hand_type_value(bottom_eval.hand_type) * 1.5
        else:
            # Stronger weight for bottom row potential
            score += self._evaluate_partial_row(hand.bottom_row, "bottom") * 0.8
        
        # Row balance bonus (avoid overloading one row early)
        score += self._evaluate_row_balance(hand) * 2.0
        
        # Enhanced fantasy land evaluation
        fl_prob = self._calculate_fantasy_land_probability(hand, node.cards_placed)
        score += fl_prob * 15.0  # Weighted by probability
        
        # Progressive penalty for risky positions
        risk_factor = self._calculate_risk_factor(hand)
        score -= risk_factor * 5.0
        
        # Position in game bonus (early vs late game)
        if node.cards_placed <= 5:
            score += 1.0  # Slight bonus for early game flexibility
        
        return score
        
    def _evaluate_complete_hand(self, hand: Hand) -> float:
        """Evaluate a complete 13-card hand."""
        if len(hand.get_all_placed_cards()) != 13:
            return 0.0  # Not actually complete
            
        score = 0.0
        
        # Evaluate each row
        top_eval = self.evaluator.evaluate_hand(hand.top_row)
        middle_eval = self.evaluator.evaluate_hand(hand.middle_row)
        bottom_eval = self.evaluator.evaluate_hand(hand.bottom_row)
        
        # Base score from hand types
        score += self._hand_type_value(top_eval.hand_type) * 1.0
        score += self._hand_type_value(middle_eval.hand_type) * 2.0
        score += self._hand_type_value(bottom_eval.hand_type) * 3.0
        
        # Add royalty bonuses
        score += top_eval.royalty_bonus
        score += middle_eval.royalty_bonus
        score += bottom_eval.royalty_bonus
        
        # Fantasy land bonus
        if self._qualifies_for_fantasy_land(hand):
            score += 20.0
            
        return score
        
    def _hand_type_value(self, hand_type) -> float:
        """Get base value for hand type."""
        # Map HandType value (0-9) to scoring value
        # HandType.value is already ordered by strength
        return float(hand_type.value)
        
    def _has_fantasy_land_potential(self, hand: Hand) -> bool:
        """Check if hand has potential for fantasy land."""
        # Need QQ+ in top or better hands in other rows
        if len(hand.top_row) >= 2:
            # Check for high pairs
            ranks = [card.rank for card in hand.top_row]
            if ranks.count('Q') >= 2 or ranks.count('K') >= 2 or ranks.count('A') >= 2:
                return True
                
        # TODO: Check for flushes/straights in progress
        return False
        
    def _qualifies_for_fantasy_land(self, hand: Hand) -> bool:
        """Check if complete hand qualifies for fantasy land."""
        if len(hand.top_row) != 3:
            return False
            
        top_eval = self.evaluator.evaluate_hand(hand.top_row)
        
        # QQ+ in top qualifies
        if top_eval.hand_type == HandType.PAIR:
            pair_rank = self._get_pair_rank(hand.top_row)
            return pair_rank >= 12  # Q=12, K=13, A=14
            
        # Trips always qualify
        return top_eval.hand_type == HandType.THREE_OF_A_KIND
        
    def _get_pair_rank(self, cards: List[Card]) -> int:
        """Get rank of pair in hand."""
        rank_counts = {}
        for card in cards:
            rank_value = card.numeric_rank
            rank_counts[rank_value] = rank_counts.get(rank_value, 0) + 1
            
        for rank, count in rank_counts.items():
            if count == 2:
                return rank
                
        return 0
        
    def _is_risky_position(self, hand: Hand) -> bool:
        """Check if current position is risky (might foul)."""
        # MVP: Simple checks
        
        # If we have cards in all rows, check progression
        if hand.top_row and hand.middle_row and hand.bottom_row:
            # Get current evaluations
            top_eval = self.evaluator.evaluate_hand(hand.top_row) if len(hand.top_row) >= 3 else None
            middle_eval = self.evaluator.evaluate_hand(hand.middle_row) if len(hand.middle_row) >= 5 else None
            bottom_eval = self.evaluator.evaluate_hand(hand.bottom_row) if len(hand.bottom_row) >= 5 else None
            
            # Check for potential fouling situations
            if top_eval and middle_eval:
                if top_eval.hand_type.value > middle_eval.hand_type.value:
                    return True
                    
            if middle_eval and bottom_eval:
                if middle_eval.hand_type.value > bottom_eval.hand_type.value:
                    return True
                    
        return False
        
    def calculate_ev_range(
        self,
        current_hand: Hand,
        remaining_deck: List[Card],
        iterations: int = 100
    ) -> Tuple[float, float, float]:
        """
        Calculate expected value with confidence intervals using Monte Carlo.
        
        MVP: Simple Monte Carlo sampling with basic statistics.
        
        Returns:
            Tuple of (mean_ev, lower_bound, upper_bound)
        """
        import random
        import statistics
        
        # For very small iterations, just do single calculation
        if iterations < 10:
            strategy = self.calculate_optimal_strategy(current_hand, remaining_deck)
            ev = strategy.expected_value.value
            margin = abs(ev) * 0.1
            return (ev, ev - margin, ev + margin)
        
        # Monte Carlo sampling
        ev_samples = []
        
        # Save original deck state
        original_deck = remaining_deck.copy()
        
        for i in range(min(iterations, 100)):  # Cap at 100 for MVP
            # Shuffle remaining deck
            shuffled_deck = original_deck.copy()
            random.shuffle(shuffled_deck)
            
            # Clear caches for fresh calculation
            if i % 10 == 0:  # Clear cache every 10 iterations
                self._position_cache.clear()
                
            # Calculate strategy with shuffled deck
            try:
                strategy = self.calculate_optimal_strategy(
                    current_hand,
                    shuffled_deck,
                    max_depth=1  # Shallower for Monte Carlo
                )
                ev_samples.append(strategy.expected_value.value)
            except Exception:
                # If calculation fails, skip this sample
                continue
                
        # If we didn't get enough samples, fallback
        if len(ev_samples) < 5:
            strategy = self.calculate_optimal_strategy(current_hand, remaining_deck)
            ev = strategy.expected_value.value
            margin = abs(ev) * 0.15
            return (ev, ev - margin, ev + margin)
            
        # Calculate statistics
        mean_ev = statistics.mean(ev_samples)
        
        if len(ev_samples) >= 30:
            # Use t-distribution for confidence interval
            std_dev = statistics.stdev(ev_samples)
            std_error = std_dev / math.sqrt(len(ev_samples))
            
            # 95% confidence interval (approximate t-value)
            t_value = 2.0  # Approximate for 30+ samples
            margin = t_value * std_error
            
            lower_bound = mean_ev - margin
            upper_bound = mean_ev + margin
        else:
            # For smaller samples, use percentiles
            sorted_samples = sorted(ev_samples)
            lower_idx = int(len(sorted_samples) * 0.1)
            upper_idx = int(len(sorted_samples) * 0.9)
            
            lower_bound = sorted_samples[lower_idx] if lower_idx < len(sorted_samples) else sorted_samples[0]
            upper_bound = sorted_samples[upper_idx - 1] if upper_idx > 0 else sorted_samples[-1]
            
        return (mean_ev, lower_bound, upper_bound)
    
    def _evaluate_partial_row(self, cards: List[Card], row_type: str) -> float:
        """Evaluate partial row for draw potential."""
        if not cards:
            return 0.0
            
        score = 0.0
        card_ranks = [c.numeric_rank for c in cards]
        card_suits = [c.suit for c in cards]
        
        # Check for pair potential
        rank_counts = {}
        for rank in card_ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
            
        # Existing pairs
        for rank, count in rank_counts.items():
            if count == 2:
                score += rank * 0.1  # Higher pairs worth more
                
        # Flush draw potential
        suit_counts = {}
        for suit in card_suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
            
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        if row_type in ["middle", "bottom"] and max_suit_count >= 3:
            score += (max_suit_count - 2) * 2.0  # Flush draw bonus
            
        # Straight draw potential (simplified)
        if row_type in ["middle", "bottom"] and len(cards) >= 3:
            sorted_ranks = sorted(set(card_ranks))
            # Check for connected cards
            for i in range(len(sorted_ranks) - 2):
                if sorted_ranks[i+2] - sorted_ranks[i] <= 4:
                    score += 1.5  # Straight draw potential
                    
        return score
    
    def _get_kicker_bonus(self, cards: List[Card]) -> float:
        """Calculate kicker bonus for pairs."""
        ranks = [c.rank_value for c in cards]
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
            
        # Find pair rank and kicker
        pair_rank = 0
        kicker_rank = 0
        for rank, count in rank_counts.items():
            if count == 2:
                pair_rank = rank
            elif count == 1 and rank > kicker_rank:
                kicker_rank = rank
                
        return kicker_rank * 0.05
    
    def _evaluate_row_balance(self, hand: Hand) -> float:
        """Evaluate how balanced the rows are."""
        row_sizes = [
            len(hand.top_row),
            len(hand.middle_row),
            len(hand.bottom_row)
        ]
        
        # Ideal progress ratios
        total_cards = sum(row_sizes)
        if total_cards == 0:
            return 1.0
            
        ideal_ratios = [3/13, 5/13, 5/13]
        actual_ratios = [size/13 for size in row_sizes]
        
        # Calculate deviation from ideal
        deviation = sum(abs(ideal - actual) 
                       for ideal, actual in zip(ideal_ratios, actual_ratios))
        
        # Return score (1.0 = perfect balance, 0.0 = worst)
        return max(0.0, 1.0 - deviation * 2.0)
    
    def _calculate_fantasy_land_probability(self, hand: Hand, cards_placed: int) -> float:
        """Calculate probability of achieving fantasy land."""
        if cards_placed >= 13:
            return 1.0 if self._qualifies_for_fantasy_land(hand) else 0.0
            
        # Simplified probability based on current top row
        if len(hand.top_row) == 0:
            return 0.15  # Base probability
            
        # Check current top row status
        top_ranks = [c.numeric_rank for c in hand.top_row]
        rank_counts = {}
        for rank in top_ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
            
        # Already have high pair?
        for rank, count in rank_counts.items():
            if count == 2 and rank >= 12:  # QQ+
                return 0.9
            elif count == 2 and rank >= 10:  # TT+
                return 0.3
                
        # High cards that could pair
        high_cards = sum(1 for rank in top_ranks if rank >= 12)
        if high_cards >= 2:
            return 0.4
        elif high_cards == 1:
            return 0.2
            
        return 0.05
    
    def _calculate_risk_factor(self, hand: Hand) -> float:
        """Calculate risk of fouling based on current position."""
        risk = 0.0
        
        # Can't assess risk without cards in rows
        if not (hand.top_row or hand.middle_row or hand.bottom_row):
            return 0.0
            
        # Evaluate current hand strengths
        strengths = []
        if len(hand.top_row) >= 3:
            top_eval = self.evaluator.evaluate_hand(hand.top_row)
            strengths.append(("top", top_eval.hand_type, top_eval.strength_value))
            
        if len(hand.middle_row) >= 5:
            middle_eval = self.evaluator.evaluate_hand(hand.middle_row)
            strengths.append(("middle", middle_eval.hand_type, middle_eval.strength_value))
            
        if len(hand.bottom_row) >= 5:
            bottom_eval = self.evaluator.evaluate_hand(hand.bottom_row)
            strengths.append(("bottom", bottom_eval.hand_type, bottom_eval.strength_value))
            
        # Check for violations or near-violations
        for i in range(len(strengths) - 1):
            row1_name, row1_type, row1_strength = strengths[i]
            row2_name, row2_type, row2_strength = strengths[i + 1]
            
            # Higher row stronger than lower? High risk!
            if row1_name == "top" and row2_name == "middle":
                if row1_type > row2_type:
                    risk += 5.0
                elif row1_type == row2_type and row1_strength > row2_strength:
                    risk += 3.0
                    
            elif row1_name == "middle" and row2_name == "bottom":
                if row1_type > row2_type:
                    risk += 5.0
                elif row1_type == row2_type and row1_strength > row2_strength:
                    risk += 3.0
                    
        return min(risk, 10.0)  # Cap risk factor
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the calculator."""
        cache_hit_rate = (self._cache_hits / (self._cache_hits + self._cache_misses) 
                         if (self._cache_hits + self._cache_misses) > 0 else 0.0)
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self._position_cache),
            "nodes_evaluated": len(self.evaluations),
            "tree_nodes": len(self.tree_builder.nodes) if self.tree_builder else 0,
            "tree_actions": len(self.tree_builder.actions) if self.tree_builder else 0
        }
    
    def clear_caches(self) -> None:
        """Clear all caches and reset statistics."""
        self._position_cache.clear()
        self.evaluations.clear()
        self._cache_hits = 0
        self._cache_misses = 0
