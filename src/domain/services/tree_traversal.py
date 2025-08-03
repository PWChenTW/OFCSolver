"""
Tree Traversal Algorithms for Game Tree

MVP implementation of essential traversal methods.
These will be used by strategy calculators.
"""

from typing import Dict, List, Optional, Callable, Any
from collections import deque

from ..base import DomainService
from ..value_objects.game_tree_node import GameTreeNode, NodeAction


class TreeTraversal(DomainService):
    """
    Provides various tree traversal algorithms.

    MVP: Basic traversal methods needed for strategy calculation.
    """

    def __init__(self, nodes: Dict[str, GameTreeNode], actions: Dict[str, NodeAction]):
        """Initialize with node and action storage."""
        self.nodes = nodes
        self.actions = actions

    def depth_first_search(
        self,
        root_id: str,
        visit_func: Callable[[GameTreeNode], Any],
        max_depth: Optional[int] = None,
    ) -> None:
        """
        Perform depth-first traversal.

        Args:
            root_id: Starting node ID
            visit_func: Function to call on each node
            max_depth: Maximum depth to traverse
        """

        def _dfs(node_id: str, depth: int):
            if max_depth is not None and depth > max_depth:
                return

            node = self.nodes.get(node_id)
            if not node:
                return

            # Visit current node
            visit_func(node)

            # Visit children
            for child_id in node.children_ids:
                _dfs(child_id, depth + 1)

        _dfs(root_id, 0)

    def breadth_first_search(
        self,
        root_id: str,
        visit_func: Callable[[GameTreeNode], Any],
        max_depth: Optional[int] = None,
    ) -> None:
        """
        Perform breadth-first traversal.

        Args:
            root_id: Starting node ID
            visit_func: Function to call on each node
            max_depth: Maximum depth to traverse
        """
        queue = deque([(root_id, 0)])

        while queue:
            node_id, depth = queue.popleft()

            if max_depth is not None and depth > max_depth:
                continue

            node = self.nodes.get(node_id)
            if not node:
                continue

            # Visit current node
            visit_func(node)

            # Add children to queue
            for child_id in node.children_ids:
                queue.append((child_id, depth + 1))

    def get_leaf_nodes(self, root_id: str) -> List[GameTreeNode]:
        """
        Get all leaf nodes from a subtree.

        Args:
            root_id: Root of subtree

        Returns:
            List of leaf nodes
        """
        leaves = []

        def collect_leaves(node: GameTreeNode):
            if node.is_leaf:
                leaves.append(node)

        self.depth_first_search(root_id, collect_leaves)
        return leaves

    def get_path_to_node(self, target_id: str) -> List[str]:
        """
        Get path from root to a specific node.

        Args:
            target_id: Target node ID

        Returns:
            List of node IDs from root to target
        """
        path = []
        current_id = target_id

        while current_id:
            path.append(current_id)
            node = self.nodes.get(current_id)
            if not node or not node.parent_id:
                break
            current_id = node.parent_id

        return list(reversed(path))

    def get_actions_on_path(self, node_id: str) -> List[NodeAction]:
        """
        Get all actions taken to reach a node.

        Args:
            node_id: Target node ID

        Returns:
            List of actions from root to node
        """
        path = self.get_path_to_node(node_id)
        actions = []

        for i in range(len(path) - 1):
            action_key = f"{path[i]}->{path[i+1]}"
            action = self.actions.get(action_key)
            if action:
                actions.append(action)

        return actions

    def count_nodes_at_depth(self, root_id: str, target_depth: int) -> int:
        """
        Count nodes at a specific depth.

        Args:
            root_id: Root node ID
            target_depth: Depth to count at

        Returns:
            Number of nodes at that depth
        """
        count = 0

        def count_at_depth(node_id: str, depth: int):
            nonlocal count
            if depth == target_depth:
                count += 1
                return  # Don't go deeper

            node = self.nodes.get(node_id)
            if node:
                for child_id in node.children_ids:
                    count_at_depth(child_id, depth + 1)

        count_at_depth(root_id, 0)
        return count

    def find_best_leaf(
        self, root_id: str, eval_func: Callable[[GameTreeNode], float]
    ) -> Optional[GameTreeNode]:
        """
        Find the best leaf node according to evaluation function.

        Args:
            root_id: Root node ID
            eval_func: Function to evaluate nodes

        Returns:
            Best leaf node or None
        """
        leaves = self.get_leaf_nodes(root_id)
        if not leaves:
            return None

        best_leaf = max(leaves, key=eval_func)
        return best_leaf
