#!/usr/bin/env python3
"""
Demo: Advanced Game Tree Features

Shows tree traversal, pruning, and transposition table usage.
"""

from datetime import datetime
import random

from src.domain.value_objects import Card, Rank, Suit, Hand
from src.domain.services.game_tree_builder import GameTreeBuilder


def create_deck():
    """Create a standard 52-card deck."""
    deck = []
    for suit in Suit:
        for rank in Rank:
            deck.append(Card(suit, rank))
    return deck


def simple_eval_function(node):
    """Simple evaluation function for testing."""
    # Prefer nodes with more cards placed
    score = node.cards_placed * 10
    
    # Bonus for not being fouled
    if not node.is_fouled:
        score += 50
        
    # Small random component
    score += random.random() * 5
    
    return score


def demo_tree_traversal():
    """Demonstrate tree traversal capabilities."""
    print("\n=== Tree Traversal Demo ===")
    
    builder = GameTreeBuilder()
    
    # Create a simple starting position
    hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.KING)],
        middle=[Card(Suit.SPADES, Rank.ACE)],
        bottom=[Card(Suit.DIAMONDS, Rank.ACE)],
        hand=[]
    )
    
    deck = create_deck()
    used_cards = hand.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards]
    random.shuffle(remaining_deck)
    
    # Build tree
    print("Building tree with depth=2...")
    root = builder.build_tree_from_position(hand, remaining_deck, max_depth=2)
    
    # Demonstrate traversal
    print(f"\nTotal nodes: {len(builder.nodes)}")
    
    # Count nodes at each depth
    for depth in range(3):
        count = builder.traversal.count_nodes_at_depth(root.node_id, depth)
        print(f"Nodes at depth {depth}: {count}")
    
    # Find best leaf
    best_leaf = builder.traversal.find_best_leaf(root.node_id, simple_eval_function)
    if best_leaf:
        print(f"\nBest leaf node: {best_leaf.node_id}")
        print(f"  Depth: {best_leaf.depth}")
        print(f"  Cards placed: {best_leaf.cards_placed}")
        
        # Show path to best leaf
        path = builder.traversal.get_path_to_node(best_leaf.node_id)
        print(f"  Path length: {len(path)}")
        
        # Show actions taken
        actions = builder.traversal.get_actions_on_path(best_leaf.node_id)
        print(f"  Actions taken: {len(actions)}")
        for i, action in enumerate(actions):
            print(f"    Step {i+1}: Placed {str(action.cards_placed[0])}, {str(action.cards_placed[1])}")


def demo_pruning():
    """Demonstrate pruning strategies."""
    print("\n=== Pruning Demo ===")
    
    builder = GameTreeBuilder()
    
    # Start with minimal cards for bigger tree
    hand = Hand.from_layout(
        top=[],
        middle=[Card(Suit.HEARTS, Rank.ACE)],
        bottom=[Card(Suit.DIAMONDS, Rank.KING)],
        hand=[]
    )
    
    deck = create_deck()
    used_cards = hand.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards]
    
    # Build larger tree
    print("Building tree with depth=3...")
    root = builder.build_tree_from_position(hand, remaining_deck[:30], max_depth=3)
    
    original_size = len(builder.nodes)
    print(f"Original tree size: {original_size} nodes")
    
    # Prune worst branches
    print("\nPruning worst 50% of branches...")
    pruned = builder.pruning.prune_worst_branches(
        root.node_id,
        simple_eval_function,
        keep_ratio=0.5
    )
    print(f"Pruned {pruned} nodes")
    print(f"Tree size after pruning: {len(builder.nodes)} nodes")
    
    # Keep only top leaves
    print("\nKeeping only top 10 leaves...")
    pruned = builder.pruning.keep_top_n_leaves(
        root.node_id,
        simple_eval_function,
        n=10
    )
    print(f"Pruned {pruned} more nodes")
    print(f"Final tree size: {len(builder.nodes)} nodes")


def demo_transposition_table():
    """Demonstrate transposition table usage."""
    print("\n=== Transposition Table Demo ===")
    
    builder = GameTreeBuilder()
    
    # Create position with symmetry potential
    hand = Hand.from_layout(
        top=[],
        middle=[],
        bottom=[Card(Suit.HEARTS, Rank.ACE), Card(Suit.DIAMONDS, Rank.ACE)],
        hand=[]
    )
    
    # Use limited deck for more transpositions
    deck = []
    # Add pairs and trips for transposition potential
    for rank in [Rank.KING, Rank.QUEEN, Rank.JACK]:
        for suit in Suit:
            deck.append(Card(suit, rank))
    
    remaining_deck = [c for c in deck if c not in hand.get_all_cards()]
    
    print(f"Using limited deck with {len(remaining_deck)} cards")
    print("Building tree with depth=3...")
    
    root = builder.build_tree_from_position(hand, remaining_deck, max_depth=3)
    
    # Show transposition statistics
    stats = builder.transposition.get_statistics()
    print(f"\nTransposition table statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Find equivalent positions
    equiv_groups = builder.transposition.find_equivalent_nodes(builder.nodes)
    print(f"\nFound {len(equiv_groups)} groups of equivalent positions")
    
    if equiv_groups:
        # Show first group
        group = equiv_groups[0]
        print(f"\nExample equivalent position group ({len(group)} nodes):")
        for node_id in group[:3]:  # Show first 3
            node = builder.nodes[node_id]
            print(f"  Node {node_id}: depth={node.depth}")


def demo_memory_efficiency():
    """Show memory efficiency improvements."""
    print("\n=== Memory Efficiency Comparison ===")
    
    # Build without transposition table
    builder1 = GameTreeBuilder()
    builder1.transposition = None  # Disable transposition
    
    hand = Hand.from_layout(top=[], middle=[], bottom=[], hand=[])
    deck = create_deck()
    
    print("Building tree WITHOUT transposition table...")
    root1 = builder1.build_tree_from_position(hand, deck[:20], max_depth=2)
    size1 = len(builder1.nodes)
    
    # Build with transposition table
    builder2 = GameTreeBuilder()
    
    print("Building tree WITH transposition table...")
    root2 = builder2.build_tree_from_position(hand, deck[:20], max_depth=2)
    size2 = len(builder2.nodes)
    
    print(f"\nResults:")
    print(f"  Without transposition: {size1} nodes")
    print(f"  With transposition: {size2} nodes")
    print(f"  Savings: {size1 - size2} nodes ({(1 - size2/size1)*100:.1f}%)")


def main():
    print("="*60)
    print("Advanced Game Tree Features Demo")
    print(f"Time: {datetime.now()}")
    print("="*60)
    
    # Run demos
    demo_tree_traversal()
    demo_pruning()
    demo_transposition_table()
    demo_memory_efficiency()
    
    print("\n" + "="*60)
    print("Advanced features completed! ✓")
    print("Tree is now ready for strategy calculations (TASK-009)")
    print("="*60)


if __name__ == "__main__":
    main()