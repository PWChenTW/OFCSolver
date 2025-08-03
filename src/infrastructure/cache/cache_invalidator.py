"""
Cache Invalidation Service for OFC Solver System.

Handles intelligent cache invalidation based on game events
and position changes.
"""

from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class InvalidationReason(Enum):
    """Reasons for cache invalidation."""

    GAME_COMPLETED = "game_completed"
    POSITION_UPDATED = "position_updated"
    ANALYSIS_OUTDATED = "analysis_outdated"
    MANUAL_FLUSH = "manual_flush"
    TTL_EXPIRED = "ttl_expired"
    STRATEGY_RECALCULATION = "strategy_recalculation"
    RULE_CHANGE = "rule_change"


@dataclass
class InvalidationEvent:
    """Event that triggers cache invalidation."""

    reason: InvalidationReason
    timestamp: datetime
    affected_keys: List[str]
    metadata: Dict[str, Any]


class CacheInvalidator:
    """
    Manages cache invalidation logic for the OFC Solver System.

    Features:
    - Event-based invalidation
    - Cascade invalidation for dependent data
    - Selective invalidation based on patterns
    - Invalidation history tracking
    """

    def __init__(self, cache_manager: CacheManager):
        """Initialize with cache manager."""
        self.cache_manager = cache_manager
        self.invalidation_history: List[InvalidationEvent] = []
        self.invalidation_rules: Dict[str, List[str]] = self._setup_invalidation_rules()

    def _setup_invalidation_rules(self) -> Dict[str, List[str]]:
        """Setup invalidation dependency rules."""
        return {
            # When a game is updated, invalidate related data
            "game:*": ["analysis:*", "strategy:*", "training:session:*"],
            # When a position is updated, invalidate analysis
            "pos:*": ["analysis:*", "strategy:*"],
            # When analysis is updated, invalidate strategies
            "analysis:*": ["strategy:*"],
            # When user data changes, invalidate their sessions
            "user:*": ["training:session:*", "training:progress:*"],
            # Stats don't trigger invalidation
            "stats:*": [],
            # Leaderboards are independent
            "leaderboard:*": [],
        }

    def invalidate_game_data(self, game_id: str) -> int:
        """
        Invalidate all cached data related to a game.

        Args:
            game_id: Game identifier

        Returns:
            Number of keys invalidated
        """
        patterns = [
            f"game:{game_id}",
            f"game:{game_id}:*",
            f"analysis:*:game_{game_id}",
            f"strategy:*:game_{game_id}",
        ]

        total_invalidated = 0
        affected_keys = []

        for pattern in patterns:
            count = self.cache_manager.invalidate_pattern(pattern)
            total_invalidated += count
            if count > 0:
                affected_keys.append(pattern)
                logger.info(f"Invalidated {count} keys for pattern: {pattern}")

        # Record invalidation event
        self._record_invalidation(
            InvalidationReason.GAME_COMPLETED, affected_keys, {"game_id": game_id}
        )

        return total_invalidated

    def invalidate_position_analysis(
        self, position_hash: str, cascade: bool = True
    ) -> int:
        """
        Invalidate analysis data for a specific position.

        Args:
            position_hash: Position hash
            cascade: Whether to cascade invalidation to dependent data

        Returns:
            Number of keys invalidated
        """
        patterns = [
            f"pos:{position_hash}",
            f"analysis:{position_hash}:*",
            f"strategy:{position_hash}",
        ]

        if cascade:
            # Add patterns for dependent data
            patterns.extend(
                [
                    f"mc:{position_hash}*",  # Monte Carlo results
                    f"training:*:{position_hash}",  # Training data using this position
                ]
            )

        total_invalidated = 0
        affected_keys = []

        for pattern in patterns:
            count = self.cache_manager.invalidate_pattern(pattern)
            total_invalidated += count
            if count > 0:
                affected_keys.append(pattern)

        self._record_invalidation(
            InvalidationReason.POSITION_UPDATED,
            affected_keys,
            {"position_hash": position_hash, "cascade": cascade},
        )

        return total_invalidated

    def invalidate_user_data(self, user_id: str) -> int:
        """
        Invalidate all cached data for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of keys invalidated
        """
        patterns = [
            f"user:{user_id}",
            f"user:{user_id}:*",
            f"training:session:*:user_{user_id}",
            f"training:progress:*:user_{user_id}",
        ]

        total_invalidated = 0
        affected_keys = []

        for pattern in patterns:
            count = self.cache_manager.invalidate_pattern(pattern)
            total_invalidated += count
            if count > 0:
                affected_keys.append(pattern)

        self._record_invalidation(
            InvalidationReason.MANUAL_FLUSH, affected_keys, {"user_id": user_id}
        )

        return total_invalidated

    def invalidate_outdated_analysis(self, max_age: timedelta) -> int:
        """
        Invalidate analysis results older than max_age.

        Args:
            max_age: Maximum age for analysis results

        Returns:
            Number of keys invalidated
        """
        # This is more complex as it requires checking timestamps
        # For MVP, we'll invalidate all analysis older than threshold
        cutoff_time = datetime.utcnow() - max_age

        # Get all analysis keys
        analysis_pattern = "analysis:*"

        # Note: In production, this would check timestamps
        # For now, we'll just clear old analysis based on TTL
        count = self.cache_manager.invalidate_pattern(analysis_pattern)

        if count > 0:
            self._record_invalidation(
                InvalidationReason.ANALYSIS_OUTDATED,
                [analysis_pattern],
                {"max_age_hours": max_age.total_seconds() / 3600},
            )

        return count

    def invalidate_by_rule_change(self, rule_type: str) -> int:
        """
        Invalidate cache when game rules change.

        Args:
            rule_type: Type of rule that changed

        Returns:
            Number of keys invalidated
        """
        # Rule changes affect all calculations
        patterns = ["analysis:*", "strategy:*", "pos:*", "mc:*"]

        total_invalidated = 0
        affected_keys = []

        for pattern in patterns:
            count = self.cache_manager.invalidate_pattern(pattern)
            total_invalidated += count
            if count > 0:
                affected_keys.append(pattern)

        self._record_invalidation(
            InvalidationReason.RULE_CHANGE, affected_keys, {"rule_type": rule_type}
        )

        logger.warning(
            f"Invalidated {total_invalidated} keys due to rule change: {rule_type}"
        )

        return total_invalidated

    def selective_invalidate(
        self, key_patterns: List[str], reason: str = "manual"
    ) -> int:
        """
        Selectively invalidate specific key patterns.

        Args:
            key_patterns: List of patterns to invalidate
            reason: Reason for invalidation

        Returns:
            Number of keys invalidated
        """
        total_invalidated = 0
        affected_keys = []

        for pattern in key_patterns:
            count = self.cache_manager.invalidate_pattern(pattern)
            total_invalidated += count
            if count > 0:
                affected_keys.append(pattern)
                logger.debug(f"Invalidated {count} keys for pattern: {pattern}")

        self._record_invalidation(
            InvalidationReason.MANUAL_FLUSH, affected_keys, {"reason": reason}
        )

        return total_invalidated

    def cascade_invalidate(self, root_key: str) -> int:
        """
        Invalidate a key and all dependent keys based on rules.

        Args:
            root_key: The root key to start invalidation from

        Returns:
            Number of keys invalidated
        """
        invalidated_keys: Set[str] = set()
        keys_to_process = [root_key]

        while keys_to_process:
            current_key = keys_to_process.pop()

            if current_key in invalidated_keys:
                continue

            # Invalidate current key
            count = self.cache_manager.invalidate_pattern(current_key)
            if count > 0:
                invalidated_keys.add(current_key)

            # Find dependent keys based on rules
            for rule_pattern, dependencies in self.invalidation_rules.items():
                if self._matches_pattern(current_key, rule_pattern):
                    # Add dependencies to process
                    for dep_pattern in dependencies:
                        # Convert dependency pattern based on current key
                        dep_key = self._resolve_dependency(current_key, dep_pattern)
                        if dep_key not in invalidated_keys:
                            keys_to_process.append(dep_key)

        total_invalidated = len(invalidated_keys)

        if total_invalidated > 0:
            self._record_invalidation(
                InvalidationReason.POSITION_UPDATED,
                list(invalidated_keys),
                {"root_key": root_key, "cascade_count": total_invalidated},
            )

        return total_invalidated

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if a key matches a pattern."""
        # Simple pattern matching - in production use regex
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return key.startswith(prefix)
        return key == pattern

    def _resolve_dependency(self, source_key: str, dep_pattern: str) -> str:
        """Resolve dependency pattern based on source key."""
        # Extract identifiers from source key
        parts = source_key.split(":")
        if len(parts) >= 2:
            key_type = parts[0]
            key_id = parts[1] if len(parts) > 1 else "*"

            # Replace wildcards in dependency pattern
            if dep_pattern.endswith("*"):
                return dep_pattern[:-1] + key_id + "*"
            else:
                return dep_pattern

        return dep_pattern

    def _record_invalidation(
        self,
        reason: InvalidationReason,
        affected_keys: List[str],
        metadata: Dict[str, Any],
    ) -> None:
        """Record invalidation event for auditing."""
        event = InvalidationEvent(
            reason=reason,
            timestamp=datetime.utcnow(),
            affected_keys=affected_keys,
            metadata=metadata,
        )

        self.invalidation_history.append(event)

        # Keep only recent history (last 1000 events)
        if len(self.invalidation_history) > 1000:
            self.invalidation_history = self.invalidation_history[-1000:]

    def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get invalidation statistics."""
        if not self.invalidation_history:
            return {"total_events": 0, "reasons": {}, "recent_events": []}

        # Count by reason
        reason_counts = {}
        for event in self.invalidation_history:
            reason = event.reason.value
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        # Get recent events
        recent_events = []
        for event in self.invalidation_history[-10:]:
            recent_events.append(
                {
                    "reason": event.reason.value,
                    "timestamp": event.timestamp.isoformat(),
                    "affected_keys": len(event.affected_keys),
                    "metadata": event.metadata,
                }
            )

        return {
            "total_events": len(self.invalidation_history),
            "reasons": reason_counts,
            "recent_events": recent_events,
        }

    def schedule_invalidation(
        self, delay: timedelta, patterns: List[str], reason: str
    ) -> None:
        """
        Schedule future invalidation (placeholder for future implementation).

        In production, this would integrate with a task queue
        like Celery or RQ for delayed execution.
        """
        logger.info(
            f"Scheduled invalidation in {delay.total_seconds()}s "
            f"for patterns: {patterns}, reason: {reason}"
        )
        # TODO: Implement with task queue

    def validate_cache_consistency(self) -> Dict[str, Any]:
        """
        Validate cache consistency (basic checks).

        Returns:
            Dictionary with validation results
        """
        issues = []

        # Check for orphaned analysis without positions
        # This is a simplified check - in production would be more thorough

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "checked_at": datetime.utcnow().isoformat(),
        }
