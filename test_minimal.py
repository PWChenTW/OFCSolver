#!/usr/bin/env python3
"""
Minimal test to verify basic functionality.
"""

from src.domain.value_objects import Card, Rank, Suit, Hand
from src.domain.services.game_tree_builder import GameTreeBuilder


def main():
    print("=== Minimal OFC Solver Test ===\n")
    
    # 1. Test basic card/hand creation
    print("1. Creating cards and hand...")
    try:
        card1 = Card(Suit.HEARTS, Rank.ACE)
        card2 = Card(Suit.SPADES, Rank.KING)
        print(f"   Created: {card1}, {card2}")
        
        hand = Hand.from_layout(
            top=[card1],
            middle=[card2],
            bottom=[],
            hand=[]
        )
        print("   ✓ Hand created successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # 2. Test game tree builder
    print("\n2. Testing game tree builder...")
    try:
        builder = GameTreeBuilder()
        
        # Create simple deck
        deck = [
            Card(Suit.HEARTS, Rank.QUEEN),
            Card(Suit.DIAMONDS, Rank.QUEEN),
            Card(Suit.CLUBS, Rank.JACK),
            Card(Suit.SPADES, Rank.TEN),
            Card(Suit.HEARTS, Rank.NINE),
            Card(Suit.DIAMONDS, Rank.EIGHT)
        ]
        
        # Build small tree
        root = builder.build_tree_from_position(hand, deck, max_depth=1)
        print(f"   Tree nodes: {len(builder.nodes)}")
        print(f"   Tree actions: {len(builder.actions)}")
        print("   ✓ Game tree built successfully")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # 3. Test tree features
    print("\n3. Checking integrated features...")
    print(f"   Transposition table: {'Yes' if builder.transposition else 'No'}")
    print(f"   Tree traversal: {'Yes' if builder.traversal else 'No'}")
    print(f"   Tree pruning: {'Yes' if builder.pruning else 'No'}")
    
    print("\n=== Basic functionality verified! ===")
    print("\nNext steps:")
    print("- TASK-011: Caching Strategy")
    print("- TASK-012: Command Handlers")
    print("- TASK-013: Query Handlers")


if __name__ == "__main__":
    main()