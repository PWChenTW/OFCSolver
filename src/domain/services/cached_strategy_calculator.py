"""
Cached Strategy Calculator Service for OFC Solver System.

Extends the base StrategyCalculator with Redis caching capabilities
for improved performance on repeated position calculations.
"""

from typing import Dict, List, Optional, Tuple, Any
import hashlib
import json
from datetime import timedelta
import logging

from .strategy_calculator import StrategyCalculator
from ..value_objects.strategy import Strategy
from ..value_objects.hand import Hand
from ..value_objects.card import Card
from ...infrastructure.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class CachedStrategyCalculator(StrategyCalculator):
    """
    Strategy calculator with Redis caching layer.

    Caches:
    - Position evaluations
    - Complete strategy calculations
    - Monte Carlo simulation results
    """

    def __init__(self, cache_manager: CacheManager, tree_builder=None, evaluator=None):
        """Initialize with cache manager."""
        super().__init__(tree_builder, evaluator)
        self.cache_manager = cache_manager
        self._cache_stats = {
            "position_hits": 0,
            "position_misses": 0,
            "strategy_hits": 0,
            "strategy_misses": 0,
            "mc_hits": 0,
            "mc_misses": 0,
        }

    def calculate_optimal_strategy(
        self, current_hand: Hand, remaining_deck: List[Card], max_depth: int = 2
    ) -> Strategy:
        """
        Calculate optimal strategy with caching.

        First checks Redis cache before calculating.
        """
        # Generate cache key for this position
        position_data = self._create_position_data(
            current_hand, remaining_deck, max_depth
        )
        position_hash = self.cache_manager.key_builder.hash_position(position_data)

        # Check cache first
        cached_analysis = self.cache_manager.get_analysis(
            position_hash, "minimax_alphabeta"
        )
        if cached_analysis:
            logger.debug(f"Strategy cache hit for position {position_hash}")
            self._cache_stats["strategy_hits"] += 1
            return self._reconstruct_strategy(cached_analysis)

        self._cache_stats["strategy_misses"] += 1
        logger.debug(f"Strategy cache miss for position {position_hash}")

        # Calculate strategy
        strategy = super().calculate_optimal_strategy(
            current_hand, remaining_deck, max_depth
        )

        # Cache the result
        analysis_result = self._create_analysis_result(strategy, position_data)
        cached = self.cache_manager.set_analysis(
            position_hash,
            "minimax_alphabeta",
            analysis_result,
            ttl=timedelta(hours=24),  # Strategies are valid for 24 hours
        )

        if cached:
            logger.debug(f"Cached strategy for position {position_hash}")

            # Also cache the position data
            self.cache_manager.set_position(position_data)

            # Cache the optimal strategy separately for quick lookup
            if strategy.recommended_actions:
                strategy_data = self._create_strategy_data(strategy)
                self.cache_manager.set_strategy(position_hash, strategy_data)

        return strategy

    def _evaluate_position(self, node) -> float:
        """
        Position evaluation with Redis caching.

        Caches individual position evaluations in Redis
        in addition to in-memory cache.
        """
        # Try in-memory cache first (fastest)
        position_key = self._get_position_key(node)
        if position_key and position_key in self._position_cache:
            self._cache_hits += 1
            return self._position_cache[position_key]

        # Try Redis cache
        if position_key:
            position_data = {
                "top_row": [str(c) for c in node.player_hand.top_row],
                "middle_row": [str(c) for c in node.player_hand.middle_row],
                "bottom_row": [str(c) for c in node.player_hand.bottom_row],
                "cards_placed": node.cards_placed,
                "is_terminal": node.is_terminal,
                "is_fouled": node.is_fouled,
            }

            position_hash = self.cache_manager.key_builder.hash_position(position_data)
            cached_position = self.cache_manager.get_position(position_hash)

            if cached_position and "evaluation" in cached_position:
                self._cache_stats["position_hits"] += 1
                eval_value = cached_position["evaluation"]
                # Also store in memory cache
                self._position_cache[position_key] = eval_value
                return eval_value

            self._cache_stats["position_misses"] += 1

        # Calculate evaluation
        eval_value = super()._evaluate_position(node)

        # Cache in Redis
        if position_key:
            position_data["evaluation"] = eval_value
            self.cache_manager.set_position(position_data, ttl=timedelta(hours=12))

        return eval_value

    def calculate_ev_range(
        self, current_hand: Hand, remaining_deck: List[Card], iterations: int = 100
    ) -> Tuple[float, float, float]:
        """
        Calculate EV range with caching of Monte Carlo results.
        """
        # Create cache key for Monte Carlo results
        mc_data = {
            "hand": self._serialize_hand(current_hand),
            "deck_size": len(remaining_deck),
            "iterations": iterations,
        }
        mc_key = hashlib.md5(json.dumps(mc_data, sort_keys=True).encode()).hexdigest()

        # Check cache
        cached_result = self.cache_manager.get(f"mc:{mc_key}")
        if cached_result:
            self._cache_stats["mc_hits"] += 1
            return tuple(cached_result)

        self._cache_stats["mc_misses"] += 1

        # Calculate
        result = super().calculate_ev_range(current_hand, remaining_deck, iterations)

        # Cache result (shorter TTL for Monte Carlo)
        self.cache_manager.cache.set(
            f"mc:{mc_key}", list(result), expire=timedelta(hours=2)
        )

        return result

    def _create_position_data(
        self, hand: Hand, remaining_deck: List[Card], max_depth: int
    ) -> Dict[str, Any]:
        """Create cacheable position data."""
        return {
            "top_row": sorted([str(c) for c in hand.top_row]),
            "middle_row": sorted([str(c) for c in hand.middle_row]),
            "bottom_row": sorted([str(c) for c in hand.bottom_row]),
            "cards_placed": len(hand.get_all_placed_cards()),
            "deck_size": len(remaining_deck),
            "max_depth": max_depth,
        }

    def _create_analysis_result(
        self, strategy: Strategy, position_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create cacheable analysis result."""
        result = {
            "position": position_data,
            "expected_value": strategy.expected_value.value,
            "confidence": strategy.confidence,
            "calculation_method": strategy.calculation_method,
            "timestamp": None,  # Will be set by Redis
        }

        if strategy.recommended_actions:
            action = strategy.recommended_actions[0]
            result["recommended_action"] = {
                "cards_to_place": [str(c) for c in action.cards_to_place],
                "card_to_discard": (
                    str(action.card_to_discard) if action.card_to_discard else None
                ),
                "expected_value": action.expected_value,
                "confidence": action.confidence,
            }

        if strategy.tree_stats:
            result["tree_stats"] = strategy.tree_stats

        return result

    def _create_strategy_data(self, strategy: Strategy) -> Dict[str, Any]:
        """Create cacheable strategy data."""
        data = {
            "expected_value": strategy.expected_value.value,
            "confidence": strategy.confidence,
            "calculation_method": strategy.calculation_method,
        }

        if strategy.recommended_actions:
            data["actions"] = []
            for action in strategy.recommended_actions:
                data["actions"].append(
                    {
                        "cards": [str(c) for c in action.cards_to_place],
                        "discard": (
                            str(action.card_to_discard)
                            if action.card_to_discard
                            else None
                        ),
                        "ev": action.expected_value,
                        "confidence": action.confidence,
                    }
                )

        return data

    def _reconstruct_strategy(self, cached_data: Dict[str, Any]) -> Strategy:
        """Reconstruct Strategy object from cached data."""
        from ..value_objects.expected_value import ExpectedValue
        from ..value_objects.strategy import ActionRecommendation

        actions = []
        if "recommended_action" in cached_data:
            action_data = cached_data["recommended_action"]
            cards = [Card.from_string(c) for c in action_data["cards_to_place"]]
            discard = (
                Card.from_string(action_data["card_to_discard"])
                if action_data["card_to_discard"]
                else None
            )

            action = ActionRecommendation(
                cards_to_place=cards,
                card_to_discard=discard,
                expected_value=action_data["expected_value"],
                confidence=action_data["confidence"],
            )
            actions.append(action)

        return Strategy(
            recommended_actions=actions,
            expected_value=ExpectedValue(cached_data["expected_value"]),
            confidence=cached_data["confidence"],
            calculation_method=cached_data["calculation_method"],
            tree_stats=cached_data.get("tree_stats", {}),
        )

    def _serialize_hand(self, hand: Hand) -> Dict[str, List[str]]:
        """Serialize hand for caching."""
        return {
            "top": sorted([str(c) for c in hand.top_row]),
            "middle": sorted([str(c) for c in hand.middle_row]),
            "bottom": sorted([str(c) for c in hand.bottom_row]),
        }

    def warm_cache_for_position(
        self, hand: Hand, remaining_deck: List[Card], variations: int = 5
    ) -> int:
        """
        Warm cache by pre-calculating common variations.

        Returns number of positions cached.
        """
        import random

        positions_cached = 0

        # Cache current position
        try:
            strategy = self.calculate_optimal_strategy(hand, remaining_deck)
            positions_cached += 1
        except Exception as e:
            logger.error(f"Failed to warm cache for base position: {e}")

        # Cache variations with different next cards
        deck_copy = remaining_deck.copy()
        random.shuffle(deck_copy)

        for i in range(min(variations, len(deck_copy))):
            # Simulate different draw orders
            varied_deck = deck_copy[i:] + deck_copy[:i]
            try:
                strategy = self.calculate_optimal_strategy(
                    hand, varied_deck, max_depth=1
                )
                positions_cached += 1
            except Exception as e:
                logger.error(f"Failed to warm cache for variation {i}: {e}")
                continue

        return positions_cached

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        perf_stats = super().get_performance_stats()

        # Add Redis cache stats
        perf_stats.update(
            {
                "redis_position_hits": self._cache_stats["position_hits"],
                "redis_position_misses": self._cache_stats["position_misses"],
                "redis_strategy_hits": self._cache_stats["strategy_hits"],
                "redis_strategy_misses": self._cache_stats["strategy_misses"],
                "redis_mc_hits": self._cache_stats["mc_hits"],
                "redis_mc_misses": self._cache_stats["mc_misses"],
                "redis_position_hit_rate": (
                    self._cache_stats["position_hits"]
                    / (
                        self._cache_stats["position_hits"]
                        + self._cache_stats["position_misses"]
                    )
                    if (
                        self._cache_stats["position_hits"]
                        + self._cache_stats["position_misses"]
                    )
                    > 0
                    else 0.0
                ),
                "redis_strategy_hit_rate": (
                    self._cache_stats["strategy_hits"]
                    / (
                        self._cache_stats["strategy_hits"]
                        + self._cache_stats["strategy_misses"]
                    )
                    if (
                        self._cache_stats["strategy_hits"]
                        + self._cache_stats["strategy_misses"]
                    )
                    > 0
                    else 0.0
                ),
            }
        )

        return perf_stats

    def invalidate_position_cache(self, hand: Hand) -> int:
        """
        Invalidate cache entries related to a specific hand position.

        Returns number of entries invalidated.
        """
        # Create patterns to match related positions
        patterns = []

        # Pattern for positions with these exact cards
        if hand.top_row:
            top_cards = sorted([str(c) for c in hand.top_row])
            patterns.append(f"pos:*top:{top_cards}*")

        if hand.middle_row:
            middle_cards = sorted([str(c) for c in hand.middle_row])
            patterns.append(f"pos:*mid:{middle_cards}*")

        if hand.bottom_row:
            bottom_cards = sorted([str(c) for c in hand.bottom_row])
            patterns.append(f"pos:*bot:{bottom_cards}*")

        # Invalidate all matching patterns
        total_invalidated = 0
        for pattern in patterns:
            count = self.cache_manager.invalidate_pattern(pattern)
            total_invalidated += count
            logger.debug(f"Invalidated {count} entries for pattern: {pattern}")

        # Also clear in-memory cache
        self.clear_caches()

        return total_invalidated

    def clear_all_caches(self) -> None:
        """Clear both in-memory and Redis caches."""
        # Clear in-memory caches
        super().clear_caches()

        # Clear Redis position and strategy caches
        patterns = ["pos:*", "strategy:*", "analysis:*", "mc:*"]
        for pattern in patterns:
            count = self.cache_manager.invalidate_pattern(pattern)
            logger.info(f"Cleared {count} Redis entries for pattern: {pattern}")

        # Reset cache statistics
        self._cache_stats = {
            "position_hits": 0,
            "position_misses": 0,
            "strategy_hits": 0,
            "strategy_misses": 0,
            "mc_hits": 0,
            "mc_misses": 0,
        }
