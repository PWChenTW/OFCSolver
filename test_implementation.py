#!/usr/bin/env python3
"""
Quick test script to verify the Card and Hand Models implementation.
"""

import sys
sys.path.append('.')

from src.domain.value_objects.card import Card, Rank, Suit
from src.domain.value_objects.hand import Hand
from src.domain.value_objects.hand_ranking import HandRanking, HandType
from src.domain.value_objects.card_position import CardPosition
from src.domain.services.hand_evaluator import HandEvaluator


def test_card_basic_functionality():
    """Test basic Card functionality."""
    print("Testing Card functionality...")
    
    # Test card creation
    card = Card.from_string("As")
    assert card.rank == Rank.ACE
    assert card.suit == Suit.SPADES
    assert str(card) == "As"
    
    # Test card comparison
    ace_spades = Card.from_string("As")
    king_hearts = Card.from_string("Kh")
    assert ace_spades > king_hearts
    
    # Test deck creation
    deck = Card.create_deck()
    assert len(deck) == 52
    
    print("✓ Card tests passed")


def test_hand_basic_functionality():
    """Test basic Hand functionality."""
    print("Testing Hand functionality...")
    
    # Test empty hand
    hand = Hand.empty()
    assert len(hand) == 0
    assert not hand.is_complete()
    
    # Test hand with cards
    cards = [Card.from_string("As"), Card.from_string("Kh"), Card.from_string("Qc")]
    hand = Hand.from_cards(cards)
    assert len(hand) == 3
    
    # Test card placement
    card_to_place = Card.from_string("As")
    new_hand = hand.place_card(card_to_place, CardPosition.TOP)
    assert len(new_hand.top_row) == 1
    assert len(new_hand.hand_cards) == 2
    
    print("✓ Hand tests passed")


def test_hand_evaluator_functionality():
    """Test HandEvaluator functionality."""
    print("Testing HandEvaluator functionality...")
    
    evaluator = HandEvaluator()
    
    # Test pair evaluation
    pair_cards = [Card.from_string("As"), Card.from_string("Ah"), Card.from_string("Kc")]
    ranking = evaluator.evaluate_hand(pair_cards)
    assert ranking.hand_type == HandType.PAIR
    assert ranking.strength_value == 14  # Ace pair
    
    # Test straight evaluation
    straight_cards = [
        Card.from_string("As"), Card.from_string("Kh"), Card.from_string("Qc"),
        Card.from_string("Jd"), Card.from_string("Ts")
    ]
    straight_ranking = evaluator.evaluate_hand(straight_cards)
    assert straight_ranking.hand_type == HandType.STRAIGHT
    assert straight_ranking.royalty_bonus == 2  # Straight royalty
    
    # Test hand comparison
    assert evaluator.compare_hands(straight_ranking, ranking) == 1  # Straight beats pair
    
    print("✓ HandEvaluator tests passed")


def test_hand_ranking_functionality():
    """Test HandRanking functionality."""
    print("Testing HandRanking functionality...")
    
    cards = [Card.from_string("As"), Card.from_string("Ah"), Card.from_string("Kc")]
    ranking = HandRanking(
        hand_type=HandType.PAIR,
        strength_value=14,
        kickers=[13],
        royalty_bonus=0,
        cards=cards
    )
    
    assert ranking.is_made_hand
    assert not ranking.is_premium_hand
    assert not ranking.has_royalty
    
    description = ranking.get_hand_description()
    assert "Pair of As" in description
    
    print("✓ HandRanking tests passed")


def test_integration():
    """Test integration between components."""
    print("Testing integration...")
    
    evaluator = HandEvaluator()
    
    # Create a complete OFC hand
    top_cards = [Card.from_string("As"), Card.from_string("Kh"), Card.from_string("Qc")]
    middle_cards = [Card.from_string("2s"), Card.from_string("2h"), Card.from_string("3c"),
                   Card.from_string("3d"), Card.from_string("4s")]
    bottom_cards = [Card.from_string("5s"), Card.from_string("5h"), Card.from_string("5c"),
                   Card.from_string("6d"), Card.from_string("6s")]
    
    hand = Hand.from_layout(top_cards, middle_cards, bottom_cards)
    assert hand.is_complete()
    
    # Test OFC validation
    is_valid = evaluator.validate_ofc_progression(top_cards, middle_cards, bottom_cards)
    assert is_valid  # Bottom (full house) > Middle (two pair) > Top (ace high)
    
    # Test fouling check with evaluator
    assert not hand.is_fouled(evaluator)
    
    print("✓ Integration tests passed")


def run_all_tests():
    """Run all tests."""
    print("Running Card and Hand Models implementation tests...\n")
    
    try:
        test_card_basic_functionality()
        test_hand_basic_functionality()
        test_hand_evaluator_functionality()
        test_hand_ranking_functionality()
        test_integration()
        
        print("\n🎉 All tests passed! Implementation is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)