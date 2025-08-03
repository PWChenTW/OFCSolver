"""
Cache Warming Service for OFC Solver System.

Pre-calculates and caches common positions and strategies
to improve performance for users.
"""

from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import random

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class WarmingStrategy(Enum):
    """Cache warming strategies."""
    POPULAR_POSITIONS = "popular_positions"
    OPENING_POSITIONS = "opening_positions"
    ENDGAME_POSITIONS = "endgame_positions"
    FANTASY_LAND = "fantasy_land"
    TRAINING_SCENARIOS = "training_scenarios"
    USER_HISTORY = "user_history"


@dataclass
class WarmingTask:
    """A cache warming task."""
    strategy: WarmingStrategy
    priority: int  # 1-10, higher is more important
    positions: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class CacheWarmer:
    """
    Manages cache warming for the OFC Solver System.
    
    Features:
    - Multiple warming strategies
    - Priority-based warming
    - Background warming
    - Progress tracking
    """
    
    def __init__(
        self,
        cache_manager: CacheManager,
        max_workers: int = 4
    ):
        """Initialize cache warmer."""
        self.cache_manager = cache_manager
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.warming_stats = {
            "total_warmed": 0,
            "failures": 0,
            "strategies": {}
        }
        self.is_warming = False
        
    def warm_opening_positions(self) -> int:
        """
        Warm cache with common opening positions.
        
        Returns:
            Number of positions warmed
        """
        logger.info("Warming cache with opening positions")
        
        # Common opening scenarios in OFC Pineapple
        opening_positions = [
            # Starting with high pairs
            {
                "top_row": [],
                "middle_row": [],
                "bottom_row": ["AA", "KK", "QQ"],
                "scenario": "high_pair_bottom"
            },
            # Starting with suited connectors
            {
                "top_row": [],
                "middle_row": ["JhTh", "Ts9s", "8d7d"],
                "bottom_row": [],
                "scenario": "suited_connectors_middle"
            },
            # Balanced start
            {
                "top_row": ["66"],
                "middle_row": ["AK"],
                "bottom_row": ["JT"],
                "scenario": "balanced_start"
            },
            # Fantasy land setup
            {
                "top_row": ["QQ"],
                "middle_row": [],
                "bottom_row": ["AK"],
                "scenario": "fantasy_land_attempt"
            }
        ]
        
        warmed_count = 0
        
        for position_template in opening_positions:
            # Generate variations
            variations = self._generate_position_variations(position_template, count=5)
            
            for position in variations:
                try:
                    # Warm this position
                    if self._warm_single_position(position):
                        warmed_count += 1
                except Exception as e:
                    logger.error(f"Failed to warm position: {e}")
                    self.warming_stats["failures"] += 1
        
        self._update_stats(WarmingStrategy.OPENING_POSITIONS, warmed_count)
        return warmed_count
    
    def warm_endgame_positions(self) -> int:
        """
        Warm cache with common endgame positions.
        
        Returns:
            Number of positions warmed
        """
        logger.info("Warming cache with endgame positions")
        
        # Common endgame scenarios (10-12 cards placed)
        endgame_positions = [
            # Close to fouling
            {
                "top_row": ["TT", "9"],
                "middle_row": ["JJ", "TT", "8"],
                "bottom_row": ["QQ", "JJ", "9"],
                "cards_placed": 11,
                "scenario": "foul_risk"
            },
            # Fantasy land qualified
            {
                "top_row": ["KK", "Q"],
                "middle_row": ["AA", "KK", "J"],
                "bottom_row": ["Straight"],
                "cards_placed": 12,
                "scenario": "fantasy_qualified"
            },
            # Fighting for royalties
            {
                "top_row": ["99", "8"],
                "middle_row": ["Flush_draw"],
                "bottom_row": ["Full_house"],
                "cards_placed": 10,
                "scenario": "royalty_hunt"
            }
        ]
        
        warmed_count = 0
        
        for position_template in endgame_positions:
            variations = self._generate_position_variations(position_template, count=3)
            
            for position in variations:
                try:
                    if self._warm_single_position(position):
                        warmed_count += 1
                except Exception as e:
                    logger.error(f"Failed to warm endgame position: {e}")
                    self.warming_stats["failures"] += 1
        
        self._update_stats(WarmingStrategy.ENDGAME_POSITIONS, warmed_count)
        return warmed_count
    
    def warm_popular_positions(self, position_hashes: List[str]) -> int:
        """
        Warm cache with popular positions from analytics.
        
        Args:
            position_hashes: List of popular position hashes
            
        Returns:
            Number of positions warmed
        """
        logger.info(f"Warming cache with {len(position_hashes)} popular positions")
        
        warmed_count = 0
        
        for position_hash in position_hashes[:100]:  # Limit to top 100
            # Check if already cached
            if self.cache_manager.get_position(position_hash):
                continue
            
            # In production, would fetch position data from database
            # For now, skip positions we don't have data for
            logger.debug(f"Would warm popular position: {position_hash}")
            
        self._update_stats(WarmingStrategy.POPULAR_POSITIONS, warmed_count)
        return warmed_count
    
    def warm_training_scenarios(self) -> int:
        """
        Warm cache with common training scenarios.
        
        Returns:
            Number of scenarios warmed
        """
        logger.info("Warming cache with training scenarios")
        
        # Common training scenarios
        training_scenarios = [
            # Pair placement decisions
            {
                "description": "Where to place AA?",
                "positions": [
                    {"top": [], "middle": [], "bottom": ["AA"]},
                    {"top": ["AA"], "middle": [], "bottom": []},
                    {"top": [], "middle": ["AA"], "bottom": []}
                ]
            },
            # Flush vs straight decisions
            {
                "description": "Build flush or straight?",
                "positions": [
                    {"top": [], "middle": ["JhTh9h"], "bottom": []},
                    {"top": [], "middle": [], "bottom": ["JhTh9h8h7h"]}
                ]
            },
            # Fantasy land decisions
            {
                "description": "Risk fantasy land?",
                "positions": [
                    {"top": ["QQ"], "middle": ["weak"], "bottom": ["weak"]},
                    {"top": ["safe"], "middle": ["strong"], "bottom": ["strong"]}
                ]
            }
        ]
        
        warmed_count = 0
        
        for scenario in training_scenarios:
            for position_template in scenario["positions"]:
                # Generate specific positions from templates
                position = self._expand_position_template(position_template)
                try:
                    if self._warm_single_position(position):
                        warmed_count += 1
                except Exception as e:
                    logger.error(f"Failed to warm training scenario: {e}")
                    self.warming_stats["failures"] += 1
        
        self._update_stats(WarmingStrategy.TRAINING_SCENARIOS, warmed_count)
        return warmed_count
    
    async def warm_cache_async(
        self,
        strategies: List[WarmingStrategy],
        max_time: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Asynchronously warm cache using specified strategies.
        
        Args:
            strategies: List of warming strategies to use
            max_time: Maximum time to spend warming
            
        Returns:
            Warming results
        """
        if self.is_warming:
            return {"error": "Warming already in progress"}
        
        self.is_warming = True
        start_time = datetime.utcnow()
        max_end_time = start_time + max_time if max_time else None
        
        results = {
            "started_at": start_time.isoformat(),
            "strategies": {},
            "total_warmed": 0
        }
        
        try:
            # Create warming tasks
            tasks = self._create_warming_tasks(strategies)
            
            # Sort by priority
            tasks.sort(key=lambda t: t.priority, reverse=True)
            
            # Process tasks
            for task in tasks:
                if max_end_time and datetime.utcnow() > max_end_time:
                    logger.info("Warming time limit reached")
                    break
                
                count = await self._process_warming_task(task)
                results["strategies"][task.strategy.value] = count
                results["total_warmed"] += count
                
        finally:
            self.is_warming = False
            
        results["completed_at"] = datetime.utcnow().isoformat()
        results["duration"] = (datetime.utcnow() - start_time).total_seconds()
        
        return results
    
    def _create_warming_tasks(
        self,
        strategies: List[WarmingStrategy]
    ) -> List[WarmingTask]:
        """Create warming tasks for specified strategies."""
        tasks = []
        
        for strategy in strategies:
            if strategy == WarmingStrategy.OPENING_POSITIONS:
                tasks.append(WarmingTask(
                    strategy=strategy,
                    priority=9,
                    positions=[],  # Will be generated
                    metadata={"type": "opening"}
                ))
            elif strategy == WarmingStrategy.ENDGAME_POSITIONS:
                tasks.append(WarmingTask(
                    strategy=strategy,
                    priority=7,
                    positions=[],
                    metadata={"type": "endgame"}
                ))
            elif strategy == WarmingStrategy.TRAINING_SCENARIOS:
                tasks.append(WarmingTask(
                    strategy=strategy,
                    priority=8,
                    positions=[],
                    metadata={"type": "training"}
                ))
            elif strategy == WarmingStrategy.FANTASY_LAND:
                tasks.append(WarmingTask(
                    strategy=strategy,
                    priority=6,
                    positions=[],
                    metadata={"type": "fantasy"}
                ))
        
        return tasks
    
    async def _process_warming_task(self, task: WarmingTask) -> int:
        """Process a single warming task."""
        logger.info(f"Processing warming task: {task.strategy.value}")
        
        if task.strategy == WarmingStrategy.OPENING_POSITIONS:
            return self.warm_opening_positions()
        elif task.strategy == WarmingStrategy.ENDGAME_POSITIONS:
            return self.warm_endgame_positions()
        elif task.strategy == WarmingStrategy.TRAINING_SCENARIOS:
            return self.warm_training_scenarios()
        elif task.strategy == WarmingStrategy.FANTASY_LAND:
            return self._warm_fantasy_land_positions()
        else:
            logger.warning(f"Unknown warming strategy: {task.strategy}")
            return 0
    
    def _warm_single_position(self, position: Dict[str, Any]) -> bool:
        """
        Warm cache for a single position.
        
        Args:
            position: Position data
            
        Returns:
            True if successfully warmed
        """
        try:
            # Create position hash
            position_hash = self.cache_manager.key_builder.hash_position(position)
            
            # Check if already cached
            if self.cache_manager.get_position(position_hash):
                return False  # Already cached
            
            # Cache the position
            self.cache_manager.set_position(position)
            
            # Also warm related analysis (placeholder)
            # In production, would calculate and cache analysis
            
            self.warming_stats["total_warmed"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to warm position: {e}")
            return False
    
    def _generate_position_variations(
        self,
        template: Dict[str, Any],
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate position variations from a template."""
        variations = []
        
        # For MVP, just return the template as-is
        # In production, would generate actual card combinations
        for i in range(count):
            variation = template.copy()
            variation["variation_id"] = i
            variations.append(variation)
        
        return variations
    
    def _expand_position_template(
        self,
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Expand a position template into actual position data."""
        # For MVP, return template with some defaults
        position = {
            "top_row": template.get("top", []),
            "middle_row": template.get("middle", []),
            "bottom_row": template.get("bottom", []),
            "cards_placed": len(template.get("top", [])) + 
                           len(template.get("middle", [])) + 
                           len(template.get("bottom", []))
        }
        
        return position
    
    def _warm_fantasy_land_positions(self) -> int:
        """Warm positions that qualify for fantasy land."""
        fantasy_positions = [
            {
                "top_row": ["QQ", "K"],
                "middle_row": ["Two_pair"],
                "bottom_row": ["Straight"],
                "scenario": "QQ_top"
            },
            {
                "top_row": ["KK", "A"],
                "middle_row": ["Trips"],
                "bottom_row": ["Flush"],
                "scenario": "KK_top"
            },
            {
                "top_row": ["AAA"],
                "middle_row": ["Full_house"],
                "bottom_row": ["Four_of_kind"],
                "scenario": "trips_top"
            }
        ]
        
        warmed_count = 0
        for position in fantasy_positions:
            if self._warm_single_position(position):
                warmed_count += 1
                
        return warmed_count
    
    def _update_stats(self, strategy: WarmingStrategy, count: int) -> None:
        """Update warming statistics."""
        strategy_name = strategy.value
        if strategy_name not in self.warming_stats["strategies"]:
            self.warming_stats["strategies"][strategy_name] = 0
        
        self.warming_stats["strategies"][strategy_name] += count
    
    def get_warming_stats(self) -> Dict[str, Any]:
        """Get cache warming statistics."""
        return {
            "total_warmed": self.warming_stats["total_warmed"],
            "failures": self.warming_stats["failures"],
            "strategies": self.warming_stats["strategies"].copy(),
            "is_warming": self.is_warming,
            "workers": self.max_workers
        }
    
    def schedule_periodic_warming(
        self,
        interval: timedelta,
        strategies: List[WarmingStrategy]
    ) -> None:
        """
        Schedule periodic cache warming (placeholder).
        
        In production, would integrate with a scheduler like APScheduler.
        """
        logger.info(
            f"Scheduled warming every {interval.total_seconds()}s "
            f"for strategies: {[s.value for s in strategies]}"
        )
        # TODO: Implement with proper scheduler
    
    def shutdown(self) -> None:
        """Shutdown the warmer and cleanup resources."""
        self.executor.shutdown(wait=True)
        logger.info("Cache warmer shut down")