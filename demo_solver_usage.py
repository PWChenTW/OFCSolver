#!/usr/bin/env python3
"""
Demo: How to use OFC Solver to get recommendations.

This shows the complete flow from input to recommendation.
"""

from datetime import datetime
import random

from src.domain.value_objects import Card, Rank, Suit, Hand
from src.domain.services.strategy_calculator import StrategyCalculator
from src.domain.services.game_tree_builder import GameTreeBuilder
from src.domain.services.pineapple_evaluator import PineappleHandEvaluator


def create_deck():
    """Create a standard 52-card deck."""
    deck = []
    for suit in Suit:
        for rank in Rank:
            deck.append(Card(suit, rank))
    return deck


def print_hand_state(hand: Hand):
    """Pretty print current hand state."""
    print("\nCurrent Position:")
    print(f"  Top:    {[str(c) for c in hand.top_row]} ({len(hand.top_row)}/3)")
    print(f"  Middle: {[str(c) for c in hand.middle_row]} ({len(hand.middle_row)}/5)")
    print(f"  Bottom: {[str(c) for c in hand.bottom_row]} ({len(hand.bottom_row)}/5)")
    print(f"  Total cards placed: {len(hand.get_all_placed_cards())}")


def get_recommendation(current_hand: Hand, dealt_cards: list[Card], remaining_deck: list[Card]):
    """
    Get solver recommendation for current position.
    
    Args:
        current_hand: Current hand state
        dealt_cards: The 3 cards just dealt
        remaining_deck: Remaining cards in deck
        
    Returns:
        Dictionary with recommendation
    """
    print(f"\nDealt 3 cards: {[str(c) for c in dealt_cards]}")
    
    # Initialize services
    evaluator = PineappleHandEvaluator()
    tree_builder = GameTreeBuilder(evaluator)
    strategy_calc = StrategyCalculator(tree_builder, evaluator)
    
    # For solver, we need to simulate having these cards available
    # This is a bit hacky but works for demo
    temp_deck = dealt_cards + remaining_deck[:17]  # Include some future cards
    
    print("\nCalculating best strategy...")
    start_time = datetime.now()
    
    # Calculate optimal strategy
    strategy = strategy_calc.calculate_optimal_strategy(
        current_hand,
        temp_deck,
        max_depth=2  # Look 2 moves ahead
    )
    
    calc_time = (datetime.now() - start_time).total_seconds() * 1000
    print(f"Calculation completed in {calc_time:.1f}ms")
    
    # Extract recommendation
    if strategy.recommended_actions:
        action = strategy.recommended_actions[0]
        
        # Find which card to discard from dealt cards
        cards_to_place = set(action.cards_to_place)
        discard = None
        for card in dealt_cards:
            if card not in cards_to_place:
                discard = card
                break
                
        result = {
            "success": True,
            "cards_to_place": action.cards_to_place,
            "card_to_discard": discard or action.card_to_discard,
            "expected_value": action.expected_value,
            "confidence": action.confidence,
            "calculation_method": strategy.calculation_method
        }
    else:
        result = {
            "success": False,
            "message": "No valid actions available",
            "expected_value": 0,
            "confidence": 0
        }
    
    # Show tree statistics
    if strategy.tree_stats:
        print(f"\nTree statistics:")
        print(f"  Nodes explored: {strategy.tree_stats['total_nodes']}")
        print(f"  Leaf nodes: {strategy.tree_stats['leaf_nodes']}")
        print(f"  Max depth: {strategy.tree_stats['max_depth']}")
    
    return result


def demo_solver_usage():
    """Demonstrate complete solver usage."""
    print("="*60)
    print("OFC Solver Usage Demo")
    print("="*60)
    
    # Scenario 1: Early game decision
    print("\n### Scenario 1: Early Game (Street 1)")
    
    # Set up initial position
    initial_hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN)],
        middle=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)],
        bottom=[Card(Suit.DIAMONDS, Rank.ACE), Card(Suit.CLUBS, Rank.ACE)],
        hand=[]
    )
    
    print_hand_state(initial_hand)
    
    # Create deck and remove used cards
    deck = create_deck()
    used_cards = initial_hand.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards]
    random.shuffle(remaining_deck)
    
    # Deal 3 cards
    dealt_cards = remaining_deck[:3]
    remaining_deck = remaining_deck[3:]
    
    # Get recommendation
    rec = get_recommendation(initial_hand, dealt_cards, remaining_deck)
    
    # Show recommendation
    print("\n📊 Recommendation:")
    if rec["success"]:
        print(f"  ✅ Place: {str(rec['cards_to_place'][0])}, {str(rec['cards_to_place'][1])}")
        print(f"  ❌ Discard: {str(rec['card_to_discard'])}")
        print(f"  📈 Expected Value: {rec['expected_value']:.2f}")
        print(f"  🎯 Confidence: {rec['confidence']*100:.0f}%")
    else:
        print(f"  ⚠️  {rec['message']}")
    
    # Scenario 2: Fantasy Land decision
    print("\n\n### Scenario 2: Fantasy Land Opportunity")
    
    fl_hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN), Card(Suit.DIAMONDS, Rank.QUEEN)],
        middle=[Card(Suit.SPADES, Rank.NINE), Card(Suit.HEARTS, Rank.NINE)],
        bottom=[Card(Suit.DIAMONDS, Rank.KING), Card(Suit.CLUBS, Rank.KING)],
        hand=[]
    )
    
    print_hand_state(fl_hand)
    print("\n💫 QQ in top - Fantasy Land qualified!")
    
    # Deal 3 cards with potential for trips
    dealt_cards = [
        Card(Suit.SPADES, Rank.QUEEN),  # Can make QQQ
        Card(Suit.CLUBS, Rank.NINE),     # Can make 999
        Card(Suit.HEARTS, Rank.FIVE)     # Random card
    ]
    
    # Get recommendation
    used_cards = fl_hand.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards and c not in dealt_cards]
    
    rec = get_recommendation(fl_hand, dealt_cards, remaining_deck)
    
    print("\n📊 Recommendation:")
    if rec["success"]:
        print(f"  ✅ Place: {str(rec['cards_to_place'][0])}, {str(rec['cards_to_place'][1])}")
        print(f"  ❌ Discard: {str(rec['card_to_discard'])}")
        print(f"  💡 Strategy: Protect Fantasy Land qualification")
    
    # Scenario 3: Late game critical decision
    print("\n\n### Scenario 3: Late Game (Street 3)")
    
    late_hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.JACK), Card(Suit.DIAMONDS, Rank.JACK)],
        middle=[Card(Suit.SPADES, Rank.KING), Card(Suit.HEARTS, Rank.KING), 
                Card(Suit.CLUBS, Rank.TWO), Card(Suit.DIAMONDS, Rank.THREE)],
        bottom=[Card(Suit.DIAMONDS, Rank.ACE), Card(Suit.CLUBS, Rank.ACE),
                Card(Suit.SPADES, Rank.FIVE), Card(Suit.HEARTS, Rank.SIX)],
        hand=[]
    )
    
    print_hand_state(late_hand)
    print("\n⚠️  Critical decision - must avoid fouling!")
    
    # Deal 3 cards
    dealt_cards = [
        Card(Suit.CLUBS, Rank.JACK),     # Can make JJJ in top
        Card(Suit.CLUBS, Rank.KING),     # Can make KKK in middle
        Card(Suit.SPADES, Rank.SEVEN)    # Can help straight in bottom
    ]
    
    # Get recommendation
    used_cards = late_hand.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards and c not in dealt_cards]
    
    rec = get_recommendation(late_hand, dealt_cards, remaining_deck)
    
    print("\n📊 Recommendation:")
    if rec["success"]:
        print(f"  ✅ Place: {str(rec['cards_to_place'][0])}, {str(rec['cards_to_place'][1])}")
        print(f"  ❌ Discard: {str(rec['card_to_discard'])}")
        print(f"  ⚡ Note: Solver considers foul risk and hand strength progression")
    
    print("\n" + "="*60)
    print("Demo completed! The solver can now give recommendations.")
    print("="*60)


if __name__ == "__main__":
    demo_solver_usage()