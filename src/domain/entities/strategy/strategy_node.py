"""
Strategy Node Entity for Game Tree Representation

The StrategyNode entity represents a node in the game tree used
for strategy analysis and decision-making in OFC positions.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass

from ...base import DomainEntity
from ...value_objects import Move, ExpectedValue, Probability
from ..game.position import Position


NodeId = str


class NodeType(Enum):
    """Types of nodes in the game tree."""
    ROOT = "root"
    DECISION = "decision"  # Player decision node
    CHANCE = "chance"      # Random event node (card draw)
    TERMINAL = "terminal"  # End of game


class EvaluationStatus(Enum):
    """Status of node evaluation."""
    PENDING = "pending"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class NodeStatistics:
    """Statistical information about a node."""
    visit_count: int = 0
    total_value: float = 0.0
    average_value: float = 0.0
    best_value: float = float('-inf')
    worst_value: float = float('inf')
    standard_deviation: float = 0.0


class StrategyNode(DomainEntity):
    """
    Represents a node in the OFC game tree for strategy analysis.
    
    Each node encapsulates a game position and maintains information
    about possible moves, child nodes, and evaluation results.
    """
    
    def __init__(
        self,
        node_id: NodeId,
        position: Position,
        node_type: NodeType = NodeType.DECISION,
        parent_node: Optional['StrategyNode'] = None,
        move_to_reach: Optional[Move] = None,
        depth: int = 0
    ):
        super().__init__(node_id)
        
        self._position = position
        self._node_type = node_type
        self._parent_node = parent_node
        self._move_to_reach = move_to_reach
        self._depth = depth
        
        # Child nodes and moves
        self._children: List['StrategyNode'] = []
        self._legal_moves: Optional[List[Move]] = None
        
        # Evaluation results
        self._evaluation_status = EvaluationStatus.PENDING
        self._expected_value: Optional[ExpectedValue] = None
        self._best_move: Optional[Move] = None
        self._move_probabilities: Dict[Move, Probability] = {}
        
        # Statistics
        self._statistics = NodeStatistics()
        
        # Search and pruning
        self._alpha: float = float('-inf')
        self._beta: float = float('inf')
        self._is_pruned = False
        self._pruning_reason: Optional[str] = None
        
        # Caching
        self._position_hash: Optional[str] = None
        self._transposition_key: Optional[str] = None
    
    @property
    def position(self) -> Position:
        """Get the position this node represents."""
        return self._position
    
    @property
    def node_type(self) -> NodeType:
        """Get the type of this node."""
        return self._node_type
    
    @property
    def parent_node(self) -> Optional['StrategyNode']:
        """Get parent node."""
        return self._parent_node
    
    @property
    def move_to_reach(self) -> Optional[Move]:
        """Get the move that led to this node."""
        return self._move_to_reach
    
    @property
    def depth(self) -> int:
        """Get depth of this node in the tree."""
        return self._depth
    
    @property
    def children(self) -> List['StrategyNode']:
        """Get child nodes."""
        return self._children.copy()
    
    @property
    def expected_value(self) -> Optional[ExpectedValue]:
        """Get expected value of this node."""
        return self._expected_value
    
    @property
    def best_move(self) -> Optional[Move]:
        """Get best move from this node."""
        return self._best_move
    
    @property
    def statistics(self) -> NodeStatistics:
        """Get node statistics."""
        return self._statistics
    
    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return len(self._children) == 0
    
    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal node."""
        return (self._node_type == NodeType.TERMINAL or 
                self._position.is_terminal_position())
    
    @property
    def is_root(self) -> bool:
        """Check if this is the root node."""
        return self._parent_node is None
    
    @property
    def is_evaluated(self) -> bool:
        """Check if node has been evaluated."""
        return self._evaluation_status == EvaluationStatus.COMPLETED
    
    @property
    def is_pruned(self) -> bool:
        """Check if node has been pruned."""
        return self._is_pruned
    
    def get_legal_moves(self) -> List[Move]:
        """Get legal moves from this position."""
        if self._legal_moves is None:
            self._legal_moves = self._position.get_legal_moves()
        return self._legal_moves.copy()
    
    def add_child(self, child_node: 'StrategyNode') -> None:
        """
        Add a child node.
        
        Args:
            child_node: Child node to add
        """
        if child_node not in self._children:
            self._children.append(child_node)
            child_node._parent_node = self
            self._increment_version()
    
    def remove_child(self, child_node: 'StrategyNode') -> None:
        """
        Remove a child node.
        
        Args:
            child_node: Child node to remove
        """
        if child_node in self._children:
            self._children.remove(child_node)
            child_node._parent_node = None
            self._increment_version()
    
    def get_child_by_move(self, move: Move) -> Optional['StrategyNode']:
        """
        Get child node reached by specific move.
        
        Args:
            move: Move to find child for
            
        Returns:
            Child node or None if not found
        """
        for child in self._children:
            if child.move_to_reach == move:
                return child
        return None
    
    def expand_node(self, max_children: Optional[int] = None) -> List['StrategyNode']:
        """
        Expand this node by creating child nodes for legal moves.
        
        Args:
            max_children: Maximum number of children to create
            
        Returns:
            List of newly created child nodes
        """
        if self.is_terminal:
            return []
        
        legal_moves = self.get_legal_moves()
        if max_children:
            legal_moves = legal_moves[:max_children]
        
        new_children = []
        
        for move in legal_moves:
            # Check if child already exists
            if self.get_child_by_move(move) is not None:
                continue
            
            # Create new position after move
            new_position = self._position.apply_move(move)
            
            # Determine child node type
            child_type = NodeType.TERMINAL if new_position.is_terminal_position() else NodeType.DECISION
            
            # Create child node
            child_id = f"{self.id}_m{len(self._children)}"
            child_node = StrategyNode(
                node_id=child_id,
                position=new_position,
                node_type=child_type,
                parent_node=self,
                move_to_reach=move,
                depth=self._depth + 1
            )
            
            self.add_child(child_node)
            new_children.append(child_node)
        
        return new_children
    
    def evaluate_node(
        self,
        expected_value: ExpectedValue,
        best_move: Optional[Move] = None,
        move_probabilities: Optional[Dict[Move, Probability]] = None
    ) -> None:
        """
        Set evaluation results for this node.
        
        Args:
            expected_value: Expected value of this position
            best_move: Best move from this position
            move_probabilities: Probability distribution over moves
        """
        self._evaluation_status = EvaluationStatus.COMPLETED
        self._expected_value = expected_value
        self._best_move = best_move
        self._move_probabilities = move_probabilities or {}
        self._increment_version()
    
    def mark_evaluation_failed(self, error_message: str) -> None:
        """Mark node evaluation as failed."""
        self._evaluation_status = EvaluationStatus.FAILED
        self._increment_version()
    
    def start_evaluation(self) -> None:
        """Mark node as being evaluated."""
        self._evaluation_status = EvaluationStatus.EVALUATING
        self._increment_version()
    
    def update_statistics(self, value: float) -> None:
        """
        Update node statistics with new value.
        
        Args:
            value: New value to incorporate
        """
        self._statistics.visit_count += 1
        self._statistics.total_value += value
        self._statistics.average_value = (
            self._statistics.total_value / self._statistics.visit_count
        )
        
        if value > self._statistics.best_value:
            self._statistics.best_value = value
        if value < self._statistics.worst_value:
            self._statistics.worst_value = value
        
        self._increment_version()
    
    def set_pruning_bounds(self, alpha: float, beta: float) -> None:
        """
        Set alpha-beta pruning bounds.
        
        Args:
            alpha: Alpha (lower) bound
            beta: Beta (upper) bound
        """
        self._alpha = alpha
        self._beta = beta
        self._increment_version()
    
    def prune_node(self, reason: str = "Alpha-beta cutoff") -> None:
        """
        Mark node as pruned.
        
        Args:
            reason: Reason for pruning
        """
        self._is_pruned = True
        self._pruning_reason = reason
        self._increment_version()
    
    def get_position_hash(self) -> str:
        """Get hash of the position for caching."""
        if self._position_hash is None:
            self._position_hash = self._position.get_position_hash()
        return self._position_hash
    
    def get_transposition_key(self) -> str:
        """Get transposition table key."""
        if self._transposition_key is None:
            # Include depth in transposition key for accurate bounds
            self._transposition_key = f"{self.get_position_hash()}_{self._depth}"
        return self._transposition_key
    
    def get_path_to_root(self) -> List['StrategyNode']:
        """Get path from this node to the root."""
        path = []
        current = self
        
        while current is not None:
            path.append(current)
            current = current._parent_node
        
        return list(reversed(path))
    
    def get_principal_variation(self) -> List[Move]:
        """Get principal variation (best move sequence) from this node."""
        variation = []
        current = self
        
        while current is not None and current._best_move is not None:
            variation.append(current._best_move)
            current = current.get_child_by_move(current._best_move)
        
        return variation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            'node_id': str(self.id),
            'position_id': str(self._position.id),
            'node_type': self._node_type.value,
            'depth': self._depth,
            'is_terminal': self.is_terminal,
            'is_leaf': self.is_leaf,
            'is_evaluated': self.is_evaluated,
            'is_pruned': self._is_pruned,
            'pruning_reason': self._pruning_reason,
            'move_to_reach': str(self._move_to_reach) if self._move_to_reach else None,
            'expected_value': (
                self._expected_value.to_dict() 
                if self._expected_value else None
            ),
            'best_move': str(self._best_move) if self._best_move else None,
            'children_count': len(self._children),
            'legal_moves_count': len(self.get_legal_moves()),
            'statistics': {
                'visit_count': self._statistics.visit_count,
                'average_value': self._statistics.average_value,
                'best_value': self._statistics.best_value,
                'worst_value': self._statistics.worst_value
            },
            'alpha': self._alpha,
            'beta': self._beta
        }
    
    def __repr__(self) -> str:
        """String representation of strategy node."""
        return (f"StrategyNode(id={self.id}, depth={self._depth}, "
                f"type={self._node_type.value}, "
                f"children={len(self._children)}, "
                f"evaluated={self.is_evaluated})")