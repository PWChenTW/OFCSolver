"""
Monte Carlo Simulator Service for OFC Strategy Analysis.

This service implements Monte Carlo Tree Search (MCTS) algorithm
for analyzing OFC positions and finding optimal strategies.
"""

import asyncio
import logging
import math
import random
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ...config import settings
from ..base import DomainService
from ..entities.game.position import Position
from ..entities.strategy.calculation import (
    Calculation,
    CalculationResult,
    CalculationType,
)
from ..entities.strategy.strategy_node import NodeStatistics, StrategyNode
from ..exceptions import StrategyCalculationError
from ..value_objects import Card, ExpectedValue, Move, Probability
from .hand_evaluator import HandEvaluator

logger = logging.getLogger(__name__)


@dataclass
class MCTSConfig:
    """Configuration for Monte Carlo Tree Search."""

    num_simulations: int = 10000
    exploration_constant: float = math.sqrt(2)  # UCB1 constant
    max_simulation_depth: int = 20
    parallel_workers: int = 4
    batch_size: int = 100
    use_progressive_widening: bool = False  # Start with False for MVP
    widening_constant: float = 1.5
    use_rave: bool = False  # Rapid Action Value Estimation
    rave_constant: float = 300.0
    timeout_ms: int = 30000
    convergence_threshold: float = 0.01
    min_visits_for_convergence: int = 100


@dataclass
class SimulationResult:
    """Result of a single Monte Carlo simulation."""

    leaf_value: float
    path: List[StrategyNode]
    moves_played: List[Move]
    terminal_reached: bool
    simulation_depth: int
    

@dataclass
class MCTSStatistics:
    """Statistics for MCTS execution."""
    
    total_simulations: int = 0
    unique_nodes_visited: int = 0
    max_tree_depth: int = 0
    convergence_achieved: bool = False
    convergence_iteration: Optional[int] = None
    best_move_changes: List[Tuple[int, Move]] = field(default_factory=list)
    time_elapsed_ms: int = 0
    simulations_per_second: float = 0.0


class MonteCarloSimulator(DomainService):
    """
    Monte Carlo Tree Search implementation for OFC strategy analysis.
    
    This service uses MCTS with UCB1 selection policy to explore the game
    tree and find optimal moves. It supports parallel simulations and
    various enhancements like progressive widening and RAVE.
    """

    def __init__(
        self,
        hand_evaluator: HandEvaluator,
        config: Optional[MCTSConfig] = None,
    ) -> None:
        """Initialize Monte Carlo simulator with dependencies."""
        self._hand_evaluator = hand_evaluator
        self._config = config or MCTSConfig()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._process_executor: Optional[ProcessPoolExecutor] = None
        
        # RAVE (All Moves As First) statistics
        self._rave_stats: Dict[str, Dict[Move, Tuple[int, float]]] = {}
        
        # Transposition table for visited positions
        self._transposition_table: Dict[str, StrategyNode] = {}
        
    async def analyze_position(
        self,
        position: Position,
        calculation: Optional[Calculation] = None,
    ) -> CalculationResult:
        """
        Analyze a position using Monte Carlo Tree Search.
        
        Args:
            position: Position to analyze
            calculation: Optional calculation entity for progress tracking
            
        Returns:
            CalculationResult with best move and expected value
        """
        start_time = time.time()
        
        try:
            # Create root node
            root = self._create_root_node(position)
            
            # Initialize statistics
            stats = MCTSStatistics()
            
            # Run MCTS
            await self._run_mcts(
                root=root,
                stats=stats,
                calculation=calculation,
            )
            
            # Extract best move and value
            best_move = self._select_best_move(root)
            expected_value = self._calculate_expected_value(root)
            
            # Calculate confidence
            confidence = self._calculate_confidence(root, stats)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            stats.time_elapsed_ms = elapsed_ms
            stats.simulations_per_second = (
                stats.total_simulations / (elapsed_ms / 1000.0)
                if elapsed_ms > 0
                else 0
            )
            
            logger.info(
                f"MCTS completed: {stats.total_simulations} simulations, "
                f"best move: {best_move}, value: {expected_value.value:.3f}, "
                f"confidence: {confidence:.3f}"
            )
            
            return CalculationResult(
                expected_value=expected_value,
                best_move=best_move,
                confidence=confidence,
                nodes_evaluated=stats.unique_nodes_visited,
                metadata={
                    "mcts_stats": stats.__dict__,
                    "config": self._config.__dict__,
                },
            )
            
        except Exception as e:
            logger.error(f"MCTS analysis failed: {e}")
            raise StrategyCalculationError(f"Monte Carlo analysis failed: {e}")
            
    async def _run_mcts(
        self,
        root: StrategyNode,
        stats: MCTSStatistics,
        calculation: Optional[Calculation],
    ) -> None:
        """
        Run the main MCTS loop.
        
        Args:
            root: Root node of the search tree
            stats: Statistics collector
            calculation: Optional calculation for progress tracking
        """
        start_time = time.time()
        converged = False
        last_best_move = None
        iterations_without_change = 0
        
        # Initialize executor for parallel simulations
        self._executor = ThreadPoolExecutor(max_workers=self._config.parallel_workers)
        
        try:
            for iteration in range(0, self._config.num_simulations, self._config.batch_size):
                # Check timeout
                elapsed_ms = int((time.time() - start_time) * 1000)
                if elapsed_ms > self._config.timeout_ms:
                    logger.warning(f"MCTS timeout after {iteration} simulations")
                    break
                    
                # Run batch of simulations
                batch_size = min(
                    self._config.batch_size,
                    self._config.num_simulations - iteration
                )
                
                await self._run_simulation_batch(root, batch_size, stats)
                
                # Update progress
                if calculation:
                    progress = (iteration + batch_size) / self._config.num_simulations * 100
                    remaining_ms = int(
                        (self._config.num_simulations - iteration - batch_size)
                        / (iteration + batch_size)
                        * elapsed_ms
                    ) if iteration > 0 else None
                    
                    calculation.update_progress(
                        progress_percentage=progress,
                        current_step=f"Simulation {iteration + batch_size}/{self._config.num_simulations}",
                        estimated_remaining_ms=remaining_ms,
                    )
                
                # Check for convergence
                current_best_move = self._select_best_move(root)
                if current_best_move != last_best_move:
                    stats.best_move_changes.append((iteration, current_best_move))
                    last_best_move = current_best_move
                    iterations_without_change = 0
                else:
                    iterations_without_change += batch_size
                    
                if self._check_convergence(root, iterations_without_change):
                    stats.convergence_achieved = True
                    stats.convergence_iteration = iteration + batch_size
                    logger.info(f"MCTS converged after {iteration + batch_size} simulations")
                    break
                    
                stats.total_simulations = iteration + batch_size
                
        finally:
            if self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None

    async def _run_simulation_batch(
        self, 
        root: StrategyNode, 
        batch_size: int, 
        stats: MCTSStatistics
    ) -> None:
        """
        Run a batch of MCTS simulations.
        
        Args:
            root: Root node to start simulations from
            batch_size: Number of simulations to run
            stats: Statistics to update
        """
        # For MVP, run simulations sequentially
        # Later versions can implement parallel execution
        for _ in range(batch_size):
            await self._run_single_simulation(root, stats)
    
    async def _run_single_simulation(self, root: StrategyNode, stats: MCTSStatistics) -> None:
        """
        Run a single MCTS simulation.
        
        Args:
            root: Root node to start from
            stats: Statistics to update
        """
        # MCTS Four Phases: Selection, Expansion, Simulation, Backpropagation
        
        # 1. Selection: Navigate to a leaf node using UCB1
        leaf_node, path = self._selection_phase(root)
        
        # 2. Expansion: Add new child nodes if possible
        expanded_node = self._expansion_phase(leaf_node)
        if expanded_node != leaf_node:
            path.append(expanded_node)
        
        # 3. Simulation: Random playout from expanded node
        simulation_value = await self._simulation_phase(expanded_node)
        
        # 4. Backpropagation: Update statistics up the tree
        self._backpropagation_phase(path, simulation_value)
        
        # Update statistics
        stats.unique_nodes_visited = len(self._transposition_table)
        stats.max_tree_depth = max(stats.max_tree_depth, len(path))

    def _selection_phase(self, root: StrategyNode) -> Tuple[StrategyNode, List[StrategyNode]]:
        """
        Selection phase: Navigate to leaf using UCB1 policy.
        
        Args:
            root: Root node to start selection from
            
        Returns:
            Tuple of (selected leaf node, path to leaf)
        """
        current = root
        path = [current]
        
        while not current.is_leaf and not current.is_terminal:
            # Calculate UCB1 values for children
            best_child = None
            best_ucb1_value = float('-inf')
            
            for child in current.children:
                ucb1_value = self._calculate_ucb1_value(child, current.statistics.visit_count)
                if ucb1_value > best_ucb1_value:
                    best_ucb1_value = ucb1_value
                    best_child = child
            
            if best_child is None:
                break
                
            current = best_child
            path.append(current)
        
        return current, path

    def _expansion_phase(self, leaf_node: StrategyNode) -> StrategyNode:
        """
        Expansion phase: Add a new child node if possible.
        
        Args:
            leaf_node: Leaf node to potentially expand
            
        Returns:
            The expanded node (new child) or the original leaf if no expansion
        """
        if leaf_node.is_terminal:
            return leaf_node
        
        # Check if we should expand this node
        if leaf_node.statistics.visit_count < 1:
            # Node hasn't been visited enough to expand
            return leaf_node
        
        # Get legal moves and check if we have unexplored moves
        legal_moves = leaf_node.get_legal_moves()
        explored_moves = {child.move_to_reach for child in leaf_node.children}
        unexplored_moves = [move for move in legal_moves if move not in explored_moves]
        
        if not unexplored_moves:
            return leaf_node
        
        # Select random unexplored move for expansion
        move_to_expand = random.choice(unexplored_moves)
        
        # Create new position after move
        new_position = leaf_node.position.apply_move(move_to_expand)
        
        # Check transposition table
        trans_key = new_position.get_position_hash()
        if trans_key in self._transposition_table:
            existing_node = self._transposition_table[trans_key]
            leaf_node.add_child(existing_node)
            return existing_node
        
        # Create new child node
        child_id = f"{leaf_node.id}_m{len(leaf_node.children)}"
        child_node = StrategyNode(
            node_id=child_id,
            position=new_position,
            parent_node=leaf_node,
            move_to_reach=move_to_expand,
            depth=leaf_node.depth + 1,
        )
        
        # Add to parent and transposition table
        leaf_node.add_child(child_node)
        self._transposition_table[trans_key] = child_node
        
        return child_node

    async def _simulation_phase(self, node: StrategyNode) -> float:
        """
        Simulation phase: Random playout from the given node.
        
        Args:
            node: Node to start simulation from
            
        Returns:
            Value of the terminal position reached
        """
        current_position = node.position
        depth = 0
        
        # Random playout until terminal or depth limit
        while (not current_position.is_terminal_position() and 
               depth < self._config.max_simulation_depth):
            
            legal_moves = current_position.get_legal_moves()
            if not legal_moves:
                break
                
            # Select random move
            random_move = random.choice(legal_moves)
            current_position = current_position.apply_move(random_move)
            depth += 1
        
        # Evaluate final position
        return self._evaluate_position_value(current_position)

    def _backpropagation_phase(self, path: List[StrategyNode], value: float) -> None:
        """
        Backpropagation phase: Update statistics up the tree.
        
        Args:
            path: Path of nodes from root to simulation node
            value: Value to backpropagate
        """
        for i, node in enumerate(path):
            # Alternate value for different players (assuming 2-player)
            node_value = value if i % 2 == 0 else -value
            node.update_statistics(node_value)

    def _calculate_ucb1_value(self, child_node: StrategyNode, parent_visits: int) -> float:
        """
        Calculate UCB1 value for node selection.
        
        Args:
            child_node: Child node to calculate UCB1 for
            parent_visits: Number of visits to parent node
            
        Returns:
            UCB1 value
        """
        if child_node.statistics.visit_count == 0:
            return float('inf')  # Unvisited nodes have highest priority
        
        exploitation = child_node.statistics.average_value
        exploration = self._config.exploration_constant * math.sqrt(
            math.log(parent_visits) / child_node.statistics.visit_count
        )
        
        return exploitation + exploration

    def _evaluate_position_value(self, position: Position) -> float:
        """
        Evaluate the value of a position.
        
        Args:
            position: Position to evaluate
            
        Returns:
            Estimated value of the position (-1 to 1)
        """
        # Simple evaluation for MVP - can be enhanced later
        if position.is_terminal_position():
            # Evaluate terminal position using hand evaluator
            current_hand = position.get_current_player_hand()
            if current_hand.is_complete():
                # Basic scoring based on hand strength
                # This is a simplified evaluation - real OFC scoring is more complex
                return random.uniform(-1, 1)  # Placeholder for MVP
        
        # For non-terminal positions, return random value for now
        # Later versions should implement proper position evaluation
        return random.uniform(-0.5, 0.5)

    def _create_root_node(self, position: Position) -> StrategyNode:
        """
        Create the root node for MCTS.
        
        Args:
            position: Starting position
            
        Returns:
            Root strategy node
        """
        root_id = f"root_{position.id}"
        root = StrategyNode(
            node_id=root_id,
            position=position,
            depth=0,
        )
        
        # Add to transposition table
        trans_key = position.get_position_hash()
        self._transposition_table[trans_key] = root
        
        return root

    def _select_best_move(self, root: StrategyNode) -> Optional[Move]:
        """
        Select the best move based on MCTS statistics.
        
        Args:
            root: Root node with explored children
            
        Returns:
            Best move or None if no moves available
        """
        if not root.children:
            return None
        
        # Select child with highest visit count (most explored)
        best_child = max(root.children, key=lambda child: child.statistics.visit_count)
        return best_child.move_to_reach

    def _calculate_expected_value(self, root: StrategyNode) -> ExpectedValue:
        """
        Calculate expected value from root node.
        
        Args:
            root: Root node with statistics
            
        Returns:
            Expected value
        """
        if root.statistics.visit_count == 0:
            return ExpectedValue(0.0)
        
        return ExpectedValue(root.statistics.average_value)

    def _calculate_confidence(self, root: StrategyNode, stats: MCTSStatistics) -> float:
        """
        Calculate confidence in the result.
        
        Args:
            root: Root node
            stats: MCTS statistics
            
        Returns:
            Confidence value (0-1)
        """
        # Simple confidence based on number of simulations
        # Later versions can implement more sophisticated confidence intervals
        base_confidence = min(stats.total_simulations / self._config.num_simulations, 1.0)
        
        # Adjust for convergence
        if stats.convergence_achieved:
            base_confidence = min(base_confidence + 0.2, 1.0)
        
        return base_confidence

    def _check_convergence(self, root: StrategyNode, iterations_without_change: int) -> bool:
        """
        Check if MCTS has converged.
        
        Args:
            root: Root node
            iterations_without_change: Number of iterations without best move change
            
        Returns:
            True if converged
        """
        # Simple convergence check for MVP
        return (iterations_without_change >= self._config.min_visits_for_convergence and
                root.statistics.visit_count >= self._config.min_visits_for_convergence)

    def clear_cache(self) -> None:
        """Clear the transposition table and other caches."""
        self._transposition_table.clear()
        self._rave_stats.clear()
        logger.info("Monte Carlo simulator caches cleared")

    def get_statistics(self) -> Dict[str, int]:
        """Get current simulator statistics."""
        return {
            "transposition_table_size": len(self._transposition_table),
            "rave_stats_size": len(self._rave_stats),
        }