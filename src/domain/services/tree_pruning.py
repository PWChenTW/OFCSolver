"""
Tree Pruning Service for Game Tree

MVP implementation of pruning strategies.
Focuses on simple but effective pruning for memory management.
"""

from typing import Dict, Set, Callable, Optional, List
import heapq

from ..base import DomainService
from ..value_objects.game_tree_node import GameTreeNode, NodeAction
from .tree_traversal import TreeTraversal


class TreePruning(DomainService):
    """
    Provides pruning strategies for game trees.
    
    MVP: Simple pruning to keep trees manageable.
    """
    
    def __init__(
        self,
        nodes: Dict[str, GameTreeNode],
        actions: Dict[str, NodeAction],
        traversal: Optional[TreeTraversal] = None
    ):
        """Initialize with node/action storage and traversal service."""
        self.nodes = nodes
        self.actions = actions
        self.traversal = traversal or TreeTraversal(nodes, actions)
        
    def prune_by_depth(self, root_id: str, max_depth: int) -> int:
        """
        Remove all nodes beyond a certain depth.
        
        Args:
            root_id: Root node ID
            max_depth: Maximum depth to keep
            
        Returns:
            Number of nodes pruned
        """
        nodes_to_remove = []
        
        def collect_deep_nodes(node: GameTreeNode):
            if node.depth > max_depth:
                nodes_to_remove.append(node.node_id)
                
        self.traversal.depth_first_search(root_id, collect_deep_nodes)
        
        # Remove nodes and their actions
        pruned_count = 0
        for node_id in nodes_to_remove:
            if node_id in self.nodes:
                # Remove actions from this node
                node = self.nodes[node_id]
                for child_id in node.children_ids:
                    action_key = f"{node_id}->{child_id}"
                    if action_key in self.actions:
                        del self.actions[action_key]
                        
                # Remove the node
                del self.nodes[node_id]
                pruned_count += 1
                
        # Update parent nodes to remove references
        self._update_parent_references(nodes_to_remove)
        
        return pruned_count
    
    def prune_worst_branches(
        self,
        root_id: str,
        eval_func: Callable[[GameTreeNode], float],
        keep_ratio: float = 0.5
    ) -> int:
        """
        Prune the worst-scoring branches.
        
        Args:
            root_id: Root node ID
            eval_func: Function to evaluate nodes
            keep_ratio: Fraction of branches to keep (0.0 to 1.0)
            
        Returns:
            Number of nodes pruned
        """
        # Get immediate children of root
        root = self.nodes.get(root_id)
        if not root or not root.children_ids:
            return 0
            
        # Evaluate each child branch
        child_scores = []
        for child_id in root.children_ids:
            child = self.nodes.get(child_id)
            if child:
                score = eval_func(child)
                child_scores.append((score, child_id))
        
        # Sort by score (best first)
        child_scores.sort(reverse=True)
        
        # Determine how many to keep
        keep_count = max(1, int(len(child_scores) * keep_ratio))
        branches_to_remove = [child_id for _, child_id in child_scores[keep_count:]]
        
        # Prune the worst branches
        pruned_count = 0
        for branch_root_id in branches_to_remove:
            pruned_count += self._prune_subtree(branch_root_id)
            
        # Update root's children list
        new_children = [child_id for _, child_id in child_scores[:keep_count]]
        self._update_node_children(root_id, new_children)
        
        return pruned_count
    
    def prune_duplicate_positions(
        self,
        root_id: str,
        position_key_func: Callable[[GameTreeNode], str]
    ) -> int:
        """
        Remove duplicate positions (simple transposition handling).
        
        Args:
            root_id: Root node ID
            position_key_func: Function to generate position key
            
        Returns:
            Number of nodes pruned
        """
        seen_positions = {}
        nodes_to_remove = []
        
        def check_duplicates(node: GameTreeNode):
            pos_key = position_key_func(node)
            if pos_key in seen_positions:
                # Keep the one with shorter path (lower depth)
                existing_node = seen_positions[pos_key]
                if node.depth > existing_node.depth:
                    nodes_to_remove.append(node.node_id)
                else:
                    nodes_to_remove.append(existing_node.node_id)
                    seen_positions[pos_key] = node
            else:
                seen_positions[pos_key] = node
                
        self.traversal.depth_first_search(root_id, check_duplicates)
        
        # Remove duplicate subtrees
        pruned_count = 0
        for node_id in nodes_to_remove:
            pruned_count += self._prune_subtree(node_id)
            
        return pruned_count
    
    def keep_top_n_leaves(
        self,
        root_id: str,
        eval_func: Callable[[GameTreeNode], float],
        n: int = 100
    ) -> int:
        """
        Keep only the top N leaf nodes by evaluation score.
        
        Args:
            root_id: Root node ID
            eval_func: Function to evaluate nodes
            n: Number of leaves to keep
            
        Returns:
            Number of nodes pruned
        """
        # Get all leaves with their scores
        leaves = self.traversal.get_leaf_nodes(root_id)
        if len(leaves) <= n:
            return 0
            
        # Score all leaves
        scored_leaves = [(eval_func(leaf), leaf.node_id) for leaf in leaves]
        
        # Keep top n
        top_n = heapq.nlargest(n, scored_leaves)
        keep_ids = {leaf_id for _, leaf_id in top_n}
        
        # Find paths to keep
        paths_to_keep = set()
        for leaf_id in keep_ids:
            path = self.traversal.get_path_to_node(leaf_id)
            paths_to_keep.update(path)
            
        # Remove nodes not on kept paths
        nodes_to_remove = []
        for node_id in self.nodes:
            if node_id not in paths_to_keep:
                nodes_to_remove.append(node_id)
                
        # Prune unwanted nodes
        pruned_count = 0
        for node_id in nodes_to_remove:
            if node_id in self.nodes:
                del self.nodes[node_id]
                pruned_count += 1
                
        self._clean_orphaned_actions()
        return pruned_count
    
    def _prune_subtree(self, root_id: str) -> int:
        """Remove a subtree starting from root_id."""
        if root_id not in self.nodes:
            return 0
            
        nodes_to_remove = []
        
        def collect_subtree(node: GameTreeNode):
            nodes_to_remove.append(node.node_id)
            
        self.traversal.depth_first_search(root_id, collect_subtree)
        
        # Remove all nodes in subtree
        pruned_count = 0
        for node_id in nodes_to_remove:
            if node_id in self.nodes:
                del self.nodes[node_id]
                pruned_count += 1
                
        # Clean up actions
        self._clean_orphaned_actions()
        
        return pruned_count
    
    def _update_parent_references(self, removed_nodes: List[str]) -> None:
        """Update parent nodes to remove references to pruned children."""
        removed_set = set(removed_nodes)
        
        for node in self.nodes.values():
            if node.children_ids:
                new_children = [
                    child_id for child_id in node.children_ids
                    if child_id not in removed_set
                ]
                if len(new_children) != len(node.children_ids):
                    self._update_node_children(node.node_id, new_children)
    
    def _update_node_children(self, node_id: str, new_children: List[str]) -> None:
        """Update a node's children list."""
        node = self.nodes.get(node_id)
        if node:
            # Create new immutable node with updated children
            updated = GameTreeNode(
                node_id=node.node_id,
                depth=node.depth,
                player_hand=node.player_hand,
                cards_placed=node.cards_placed,
                dealt_cards=node.dealt_cards,
                possible_actions=node.possible_actions,
                parent_id=node.parent_id,
                children_ids=new_children,
                is_terminal=node.is_terminal or len(new_children) == 0,
                is_fouled=node.is_fouled
            )
            self.nodes[node_id] = updated
    
    def _clean_orphaned_actions(self) -> None:
        """Remove actions that reference non-existent nodes."""
        actions_to_remove = []
        
        for action_key in self.actions:
            from_id, to_id = action_key.split('->')
            if from_id not in self.nodes or to_id not in self.nodes:
                actions_to_remove.append(action_key)
                
        for action_key in actions_to_remove:
            del self.actions[action_key]