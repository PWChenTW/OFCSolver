"""
Fantasy Land Strategy Analyzer

MVP implementation for analyzing Fantasy Land entry strategies.
Focuses on simple heuristics and basic EV calculation.
"""

from typing import List, Dict, Tuple, Optional
from collections import Counter

from ..base import DomainService
from ..value_objects import Card, Rank
from .pineapple_evaluator import PineappleHandEvaluator


class FantasyLandStrategyAnalyzer(DomainService):
    """
    Simple strategy analyzer for Fantasy Land optimization.

    MVP version using basic heuristics:
    - Prioritize QQ+ in early streets
    - Balance foul risk vs FL entry
    - Simple EV calculations
    """

    def __init__(self, evaluator: Optional[PineappleHandEvaluator] = None):
        """Initialize with hand evaluator."""
        self.evaluator = evaluator or PineappleHandEvaluator()

        # Simple risk weights (can be tuned later)
        self.FOUL_PENALTY = -6.0  # Losing all 3 rows
        self.FL_ENTRY_BONUS = 10.0  # Conservative estimate
        self.QQ_PROBABILITY_THRESHOLD = 0.15  # Min probability to pursue

    def analyze_top_row_placement(
        self,
        current_top: List[Card],
        candidate_card: Card,
        remaining_streets: int,
    ) -> Dict[str, float]:
        """
        Analyze placing a card in top row for FL potential.

        Returns dict with:
        - fl_probability: Chance of achieving QQ+
        - risk_score: Risk of fouling
        - ev_score: Simple expected value
        - recommendation: -1 to 1 (-1=avoid, 0=neutral, 1=recommend)
        """
        analysis = {
            "fl_probability": 0.0,
            "risk_score": 0.0,
            "ev_score": 0.0,
            "recommendation": 0.0,
        }

        # Check current state
        if len(current_top) >= 3:
            return analysis  # Row full

        # Simulate placing the card
        test_top = current_top + [candidate_card]

        # Calculate FL probability
        fl_prob = self._calculate_fl_probability(test_top, remaining_streets)
        analysis["fl_probability"] = fl_prob

        # Simple risk assessment
        risk = self._assess_foul_risk(test_top, candidate_card)
        analysis["risk_score"] = risk

        # Basic EV calculation
        ev = (fl_prob * self.FL_ENTRY_BONUS) - (risk * self.FOUL_PENALTY)
        analysis["ev_score"] = ev

        # Simple recommendation
        if fl_prob >= self.QQ_PROBABILITY_THRESHOLD and risk < 0.3:
            analysis["recommendation"] = min(1.0, fl_prob * 2)
        elif risk > 0.5:
            analysis["recommendation"] = -1.0
        else:
            analysis["recommendation"] = ev / 10.0  # Normalize

        return analysis

    def _calculate_fl_probability(
        self,
        current_top: List[Card],
        remaining_streets: int,
    ) -> float:
        """
        Calculate probability of achieving QQ+ in top row.

        Simplified calculation based on:
        - Current cards
        - Remaining opportunities
        - Basic combinatorics
        """
        if len(current_top) >= 3:
            # Check if already qualified
            if self.evaluator.is_fantasy_land_qualifying(current_top):
                return 1.0
            return 0.0

        # Count current pairs/trips potential
        rank_counts = Counter(card.rank for card in current_top)

        # Already have QQ+
        for rank, count in rank_counts.items():
            if rank.numeric_value >= 12 and count >= 2:  # Q=12
                return 0.95  # Very likely to maintain

        # Have one Q or better
        high_cards = sum(1 for card in current_top if card.rank.numeric_value >= 12)

        # Simplified probability based on remaining cards
        cards_needed = 3 - len(current_top)
        cards_per_street = 2  # Pineapple: place 2 from 3
        opportunities = min(cards_needed, remaining_streets * cards_per_street)

        if high_cards == 0:
            # Need to get QQ+ from scratch
            base_prob = 0.05 * opportunities
        elif high_cards == 1:
            # Need to pair our Q/K/A
            base_prob = 0.15 * opportunities
        else:
            # Multiple high cards
            base_prob = 0.25 * opportunities

        return min(base_prob, 0.8)  # Cap at 80%

    def _assess_foul_risk(
        self,
        test_top: List[Card],
        candidate_card: Card,
    ) -> float:
        """
        Assess risk of fouling by placing card in top.

        Simplified risk based on:
        - Card strength
        - Current hand strength
        - General heuristics
        """
        if len(test_top) > 3:
            return 0.0  # Can't place here

        # High cards in top are generally risky
        card_strength = candidate_card.rank.numeric_value / 14.0

        # Current hand strength
        if len(test_top) >= 2:
            rank_counts = Counter(card.rank for card in test_top)
            max_count = max(rank_counts.values())

            if max_count >= 2:
                # Already have a pair
                pair_rank = max(
                    rank for rank, count in rank_counts.items() if count >= 2
                )
                if pair_rank.numeric_value >= 10:  # TT+
                    return 0.2  # Lower risk with strong pair

        # Base risk increases with card strength
        base_risk = card_strength * 0.4

        # Adjust for street
        if len(test_top) == 2:
            # Last card, higher risk
            base_risk *= 1.5

        return min(base_risk, 0.9)

    def recommend_fantasy_land_play(
        self,
        dealt_cards: List[Card],
    ) -> Dict[str, any]:
        """
        Recommend optimal play for Fantasy Land (14 cards).

        Simple algorithm:
        1. Find best bottom row (5 cards)
        2. Find best middle row from remaining
        3. Place rest in top, verify QQ+ for staying
        """
        recommendation = {
            "top": [],
            "middle": [],
            "bottom": [],
            "discarded": None,
            "can_stay": False,
            "expected_royalties": 0,
        }

        # Find strongest possible hands
        all_combinations = self._find_best_combination(dealt_cards)

        if all_combinations:
            best = all_combinations[0]  # Already sorted by score
            recommendation.update(best)

        return recommendation

    def _find_best_combination(
        self,
        cards: List[Card],
    ) -> List[Dict]:
        """
        Find best card combination for Fantasy Land.

        Simplified: Try a few good combinations, not exhaustive search.
        """
        # This is a simplified version
        # In practice, would need more sophisticated algorithm

        # For MVP, just return a valid combination
        if len(cards) != 14:
            return []

        # Sort by rank for easier processing
        sorted_cards = sorted(cards, key=lambda c: c.rank.numeric_value, reverse=True)

        # Simple heuristic: put high pairs in top for staying
        # Put flush/straight potential in middle/bottom

        result = {
            "top": sorted_cards[:3],
            "middle": sorted_cards[3:8],
            "bottom": sorted_cards[8:13],
            "discarded": sorted_cards[13],
            "can_stay": False,
            "expected_royalties": 0,
        }

        # Check if can stay
        top_eval = self.evaluator.evaluate_hand(result["top"])
        middle_eval = self.evaluator.evaluate_hand(result["middle"])
        bottom_eval = self.evaluator.evaluate_hand(result["bottom"])

        # Calculate royalties
        royalties = (
            top_eval.royalty_bonus
            + middle_eval.royalty_bonus
            + bottom_eval.royalty_bonus
        )
        result["expected_royalties"] = royalties

        # Check stay conditions (simplified)
        from ..value_objects.hand_ranking import HandType

        if (
            top_eval.hand_type == HandType.THREE_OF_A_KIND
            or middle_eval.hand_type.value >= HandType.FULL_HOUSE.value
            or bottom_eval.hand_type.value >= HandType.FOUR_OF_A_KIND.value
        ):
            result["can_stay"] = True

        return [result]

    def calculate_street_priorities(
        self,
        current_state: Dict[str, List[Card]],
        street: int,
    ) -> Dict[str, float]:
        """
        Calculate priorities for each row in current street.

        Returns priority scores for top/middle/bottom.
        """
        priorities = {
            "top": 0.0,
            "middle": 0.0,
            "bottom": 0.0,
        }

        remaining_streets = 4 - street

        # Early streets: prioritize top for FL
        if street <= 1 and len(current_state.get("top", [])) < 2:
            priorities["top"] = 0.7
            priorities["middle"] = 0.2
            priorities["bottom"] = 0.1

        # Middle streets: balance
        elif street == 2:
            priorities["top"] = 0.4
            priorities["middle"] = 0.4
            priorities["bottom"] = 0.2

        # Late streets: avoid fouling
        else:
            priorities["top"] = 0.1
            priorities["middle"] = 0.3
            priorities["bottom"] = 0.6

        return priorities
