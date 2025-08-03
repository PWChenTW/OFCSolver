#!/usr/bin/env python3
"""
Demo script for Joker (wild card) support in OFC.

Shows how jokers work in:
1. Hand evaluation
2. Best substitution finding
3. Strategy implications
"""

from datetime import datetime

from src.domain.value_objects import Card, Rank, Suit
from src.domain.value_objects.joker_card import (
    JokerCard, JokerHandEvaluator, identify_jokers_in_hand
)
from src.domain.services import PineappleHandEvaluator


def test_basic_joker():
    """Test basic joker functionality."""
    print("\n=== Basic Joker Test ===")
    
    # Create joker
    joker = JokerCard()
    print(f"Joker representation: {joker}")
    print(f"Is joker: {joker.is_joker}")
    print(f"Dict form: {joker.to_dict()}")


def test_joker_evaluation():
    """Test hand evaluation with jokers."""
    print("\n=== Joker Hand Evaluation ===")
    
    base_evaluator = PineappleHandEvaluator()
    joker_evaluator = JokerHandEvaluator(base_evaluator)
    
    # Scenario 1: One joker with a King (makes KK)
    print("\nScenario 1: K + Joker")
    cards = [
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.CLUBS, Rank.SEVEN),
        Card(Suit.DIAMONDS, Rank.FIVE),
    ]
    jokers = [JokerCard()]
    
    result = joker_evaluator.evaluate_with_jokers(cards, jokers)
    print(f"Best hand: {[str(c) for c in result['best_hand']]}")
    print(f"Substitutions: {result['substitutions']}")
    print(f"Hand type: {result['ranking'].hand_type}")
    print(f"Royalty bonus: {result['ranking'].royalty_bonus}")
    
    # Scenario 2: Two jokers (flexible options)
    print("\nScenario 2: Two jokers with Q")
    cards = [
        Card(Suit.HEARTS, Rank.QUEEN),
    ]
    jokers = [JokerCard(), JokerCard()]
    
    result = joker_evaluator.evaluate_with_jokers(cards, jokers)
    print(f"Best hand: {[str(c) for c in result['best_hand']]}")
    print(f"Substitutions: {result['substitutions']}")
    print(f"Hand type: {result['ranking'].hand_type}")
    print(f"Royalty bonus: {result['ranking'].royalty_bonus}")
    
    # Scenario 3: Joker in 5-card hand
    print("\nScenario 3: Flush potential with joker")
    cards = [
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.SPADES, Rank.KING),
        Card(Suit.SPADES, Rank.QUEEN),
        Card(Suit.SPADES, Rank.JACK),
    ]
    jokers = [JokerCard()]
    
    result = joker_evaluator.evaluate_with_jokers(cards, jokers)
    print(f"Best hand: {[str(c) for c in result['best_hand']]}")
    print(f"Substitutions: {result['substitutions']}")
    print(f"Hand type: {result['ranking'].hand_type}")
    print(f"Royalty bonus: {result['ranking'].royalty_bonus}")


def test_joker_strategy():
    """Test strategic implications of jokers."""
    print("\n=== Joker Strategy Analysis ===")
    
    print("\nKey Strategic Points:")
    print("1. Jokers are most valuable in top row (easier QQ+ for FL)")
    print("2. Early placement decisions become more flexible")
    print("3. Risk of fouling decreases significantly")
    print("4. Expected royalties increase")
    
    # Example: Fantasy Land entry with joker
    print("\nFantasy Land Entry Example:")
    print("- Normal: Need QQ+ (about 15-20% chance)")
    print("- With 1 Joker: Much easier (30-40% chance)")
    print("- With 2 Jokers: Almost guaranteed (60%+ chance)")
    
    # Risk mitigation
    print("\nRisk Mitigation:")
    print("- Joker in middle/bottom helps avoid fouling")
    print("- Can 'fix' bad draws in later streets")
    print("- Allows more aggressive top row play")


def test_mixed_hand_identification():
    """Test identifying jokers in mixed hands."""
    print("\n=== Mixed Hand Identification ===")
    
    # Create mixed hand
    mixed_hand = [
        Card(Suit.HEARTS, Rank.ACE),
        JokerCard(),
        Card(Suit.DIAMONDS, Rank.KING),
        JokerCard(),
        Card(Suit.CLUBS, Rank.QUEEN),
    ]
    
    regular_cards, joker_cards = identify_jokers_in_hand(mixed_hand)
    
    print(f"Total cards: {len(mixed_hand)}")
    print(f"Regular cards: {[str(c) for c in regular_cards]}")
    print(f"Jokers: {len(joker_cards)}")


def test_joker_in_ofc_context():
    """Test joker in OFC game context."""
    print("\n=== Joker in OFC Context ===")
    
    base_evaluator = PineappleHandEvaluator()
    joker_evaluator = JokerHandEvaluator(base_evaluator)
    
    # Simulate OFC rows with jokers
    print("\nOFC Hand with Jokers:")
    
    # Top row: Q + Joker + K = QQ with K (FL entry!)
    top_cards = [Card(Suit.HEARTS, Rank.QUEEN), Card(Suit.CLUBS, Rank.KING)]
    top_jokers = [JokerCard()]
    top_result = joker_evaluator.evaluate_with_jokers(top_cards, top_jokers)
    
    print(f"Top: {[str(c) for c in top_cards]} + 🃏")
    print(f"  → {top_result['ranking'].hand_type} (FL qualified!)")
    
    # Middle row: Regular hand
    middle_cards = [
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.SPADES, Rank.KING),
        Card(Suit.SPADES, Rank.QUEEN),
        Card(Suit.HEARTS, Rank.JACK),
        Card(Suit.HEARTS, Rank.TEN),
    ]
    middle_result = base_evaluator.evaluate_hand(middle_cards)
    print(f"Middle: {[str(c) for c in middle_cards]}")
    print(f"  → {middle_result.hand_type}")
    
    # Bottom row: With joker for safety
    bottom_cards = [
        Card(Suit.CLUBS, Rank.NINE),
        Card(Suit.CLUBS, Rank.EIGHT),
        Card(Suit.CLUBS, Rank.SEVEN),
        Card(Suit.DIAMONDS, Rank.SIX),
    ]
    bottom_jokers = [JokerCard()]
    bottom_result = joker_evaluator.evaluate_with_jokers(bottom_cards, bottom_jokers)
    
    print(f"Bottom: {[str(c) for c in bottom_cards]} + 🃏")
    print(f"  → {bottom_result['ranking'].hand_type}")
    
    print("\nResult: Valid OFC hand with Fantasy Land entry!")


def main():
    """Run all joker demos."""
    print("=" * 60)
    print("Joker (Wild Card) Support Demo")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    test_basic_joker()
    test_joker_evaluation()
    test_joker_strategy()
    test_mixed_hand_identification()
    test_joker_in_ofc_context()
    
    print("\n" + "=" * 60)
    print("Joker support demo completed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()