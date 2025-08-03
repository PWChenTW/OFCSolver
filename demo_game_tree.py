#!/usr/bin/env python3
"""
Demo: Game Tree Builder for Pineapple OFC

Shows basic game tree construction and traversal.
MVP implementation - simple but functional.
"""

from datetime import datetime
import random

from src.domain.value_objects import (
    Card, Rank, Suit, Hand, CardPosition
)
from src.domain.services.game_tree_builder import GameTreeBuilder


def create_deck():
    """Create a standard 52-card deck."""
    deck = []
    for suit in Suit:
        for rank in Rank:
            deck.append(Card(suit, rank))
    return deck


def create_sample_hand():
    """Create a sample mid-game hand for testing."""
    # Simulate a hand after initial placement
    hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN)],  # 1 card in top
        middle=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)],  # 2 in middle
        bottom=[Card(Suit.DIAMONDS, Rank.TEN), Card(Suit.CLUBS, Rank.TEN)],  # 2 in bottom
        hand=[]
    )
    return hand


def print_node_info(builder, node_id):
    """Print information about a specific node."""
    node = builder.nodes.get(node_id)
    if not node:
        return
        
    print(f"\nNode {node_id}:")
    print(f"  Depth: {node.depth}")
    print(f"  Cards placed: {node.cards_placed}")
    print(f"  Terminal: {node.is_terminal}")
    print(f"  Fouled: {node.is_fouled}")
    
    if node.dealt_cards:
        print(f"  Dealt: {[str(c) for c in node.dealt_cards]}")
    
    if node.possible_actions:
        print(f"  Possible actions: {len(node.possible_actions)}")
        
    print(f"  Children: {len(node.children_ids)}")


def demo_basic_tree_building():
    """Demonstrate basic tree building."""
    print("\n=== Basic Tree Building ===")
    
    # Create builder and initial setup
    builder = GameTreeBuilder()
    hand = create_sample_hand()
    deck = create_deck()
    
    # Remove cards already in hand
    used_cards = hand.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards]
    
    # Shuffle for realism
    random.shuffle(remaining_deck)
    
    print(f"Starting hand has {len(used_cards)} cards")
    print(f"Remaining deck has {len(remaining_deck)} cards")
    
    # Show current hand state
    print(f"\nCurrent hand:")
    print(f"  Top: {len(hand.top_row)} cards - {[str(c) for c in hand.top_row]}")
    print(f"  Middle: {len(hand.middle_row)} cards - {[str(c) for c in hand.middle_row]}")
    print(f"  Bottom: {len(hand.bottom_row)} cards - {[str(c) for c in hand.bottom_row]}")
    
    # Build tree with depth 1 (just one street ahead)
    print("\nBuilding tree with depth=1...")
    root = builder.build_tree_from_position(hand, remaining_deck, max_depth=1)
    
    # Get statistics
    stats = builder.get_tree_stats(root)
    print(f"\nTree statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
        
    # Show root node
    print_node_info(builder, root.node_id)
    
    # Debug: check if any children were created
    if len(builder.nodes) > 1:
        print(f"\nTotal nodes created: {len(builder.nodes)}")
    else:
        print("\nDEBUG: No children created. Checking placement logic...")
        
    # Show first few children
    print("\nFirst 3 child nodes:")
    for child_id in root.children_ids[:3]:
        print_node_info(builder, child_id)


def demo_deeper_tree():
    """Demonstrate deeper tree building."""
    print("\n=== Deeper Tree Building ===")
    
    # Start with fewer cards for deeper tree
    hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN)],
        middle=[Card(Suit.SPADES, Rank.ACE)],
        bottom=[Card(Suit.DIAMONDS, Rank.KING)],
        hand=[]
    )
    
    builder = GameTreeBuilder()
    deck = create_deck()
    used_cards = hand.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards]
    random.shuffle(remaining_deck)
    
    print(f"Starting with only {len(used_cards)} cards for deeper tree")
    
    # Build deeper tree
    print("\nBuilding tree with depth=2...")
    root = builder.build_tree_from_position(hand, remaining_deck, max_depth=2)
    
    stats = builder.get_tree_stats(root)
    print(f"\nDeeper tree statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
        
    # Show branching factor
    if root.children_ids:
        first_child = builder.nodes[root.children_ids[0]]
        print(f"\nBranching factor example:")
        print(f"  Root has {len(root.children_ids)} children")
        print(f"  First child has {len(first_child.children_ids)} children")


def demo_action_tracking():
    """Demonstrate action tracking in the tree."""
    print("\n=== Action Tracking ===")
    
    builder = GameTreeBuilder()
    hand = create_sample_hand()
    deck = create_deck()
    used_cards = hand.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards]
    
    # Build small tree
    root = builder.build_tree_from_position(hand, remaining_deck[:12], max_depth=1)
    
    print(f"Total actions stored: {len(builder.actions)}")
    
    # Show first few actions
    print("\nFirst 3 actions:")
    for i, (key, action) in enumerate(list(builder.actions.items())[:3]):
        print(f"\nAction {i+1}: {key}")
        print(f"  Cards placed: {str(action.cards_placed[0])}, {str(action.cards_placed[1])}")
        print(f"  Card discarded: {str(action.card_discarded)}")


def demo_memory_efficiency():
    """Demonstrate memory considerations."""
    print("\n=== Memory Efficiency ===")
    
    print("Tree size grows exponentially with depth:")
    print("Depth 1: ~3 nodes (3 ways to pick 2 from 3)")
    print("Depth 2: ~3 * 3 = 9 leaf nodes")
    print("Depth 3: ~3 * 3 * 3 = 27 leaf nodes")
    print("...")
    print("Depth 8 (full game): ~3^8 = 6,561 leaf nodes")
    
    print("\nMVP approach: Limit depth to 2-3 for practical use")
    print("Future optimization: Add transposition table")
    print("Future optimization: Add pruning based on hand strength")


def main():
    print("="*60)
    print("Game Tree Builder Demo")
    print(f"Time: {datetime.now()}")
    print("="*60)
    
    # Run demos
    demo_basic_tree_building()
    demo_deeper_tree()
    demo_action_tracking()
    demo_memory_efficiency()
    
    print("\n" + "="*60)
    print("Game tree builder MVP completed! ✓")
    print("Next steps: Add evaluation and search algorithms")
    print("="*60)


if __name__ == "__main__":
    main()