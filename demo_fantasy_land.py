#!/usr/bin/env python3
"""
Demo script for Fantasy Land functionality.

Tests the MVP Fantasy Land implementation:
1. Entry qualification (QQ+)
2. 14-card dealing
3. Stay qualification
4. State management
"""

from datetime import datetime
from uuid import uuid4

from src.domain.value_objects import (
    Card, Rank, Suit, FantasyLandState
)
from src.domain.services import PineappleFantasyLandManager


def create_test_cards():
    """Create cards for testing Fantasy Land scenarios."""
    return {
        # QQ for Fantasy Land entry
        "QH": Card(Suit.HEARTS, Rank.QUEEN),
        "QD": Card(Suit.DIAMONDS, Rank.QUEEN),
        "QC": Card(Suit.CLUBS, Rank.QUEEN),
        "KC": Card(Suit.CLUBS, Rank.KING),
        
        # JJ for weak pair
        "JH": Card(Suit.HEARTS, Rank.JACK),
        "JD": Card(Suit.DIAMONDS, Rank.JACK),
        
        # Trips for staying in FL
        "AH": Card(Suit.HEARTS, Rank.ACE),
        "AD": Card(Suit.DIAMONDS, Rank.ACE),
        "AC": Card(Suit.CLUBS, Rank.ACE),
        
        # Full house for middle
        "KH": Card(Suit.HEARTS, Rank.KING),
        "KD": Card(Suit.DIAMONDS, Rank.KING),
        "KS": Card(Suit.SPADES, Rank.KING),
        "7H": Card(Suit.HEARTS, Rank.SEVEN),
        "7D": Card(Suit.DIAMONDS, Rank.SEVEN),
        
        # Quads for bottom
        "9H": Card(Suit.HEARTS, Rank.NINE),
        "9D": Card(Suit.DIAMONDS, Rank.NINE),
        "9C": Card(Suit.CLUBS, Rank.NINE),
        "9S": Card(Suit.SPADES, Rank.NINE),
        "8C": Card(Suit.CLUBS, Rank.EIGHT),
    }


def test_fantasy_land_entry():
    """Test Fantasy Land entry qualification."""
    print("\n=== Testing Fantasy Land Entry ===")
    
    manager = PineappleFantasyLandManager()
    cards = create_test_cards()
    
    # Test QQ+ qualifies
    top_qq = [cards["QH"], cards["QD"], cards["KC"]]
    qualifies = manager.check_entry_qualification(top_qq)
    print(f"QQ with K kicker: {qualifies} (should be True)")
    
    # Test lower pair doesn't qualify
    top_77 = [cards["7H"], cards["7D"], cards["KC"]]
    qualifies = manager.check_entry_qualification(top_77)
    print(f"77 with K kicker: {qualifies} (should be False)")
    
    # Test trips qualify
    top_aaa = [cards["AH"], cards["AD"], cards["AC"]]
    qualifies = manager.check_entry_qualification(top_aaa)
    print(f"AAA trips: {qualifies} (should be True)")


def test_fantasy_land_state():
    """Test Fantasy Land state management."""
    print("\n=== Testing Fantasy Land State ===")
    
    player_id = uuid4()
    
    # Initial state
    state = FantasyLandState.create_initial(player_id)
    print(f"Initial state: active={state.is_active}, count={state.consecutive_count}")
    
    # Enter Fantasy Land
    state = state.enter_fantasy_land(current_round=1)
    print(f"After entry: active={state.is_active}, round={state.entry_round}, count={state.consecutive_count}")
    
    # Stay in Fantasy Land
    state = state.enter_fantasy_land(current_round=2)
    print(f"After staying: active={state.is_active}, round={state.entry_round}, count={state.consecutive_count}")
    
    # Exit Fantasy Land
    state = state.exit_fantasy_land()
    print(f"After exit: active={state.is_active}, count={state.consecutive_count}")


def test_stay_qualification():
    """Test staying in Fantasy Land."""
    print("\n=== Testing Stay Qualification ===")
    
    manager = PineappleFantasyLandManager()
    cards = create_test_cards()
    
    # Stay conditions are same as entry - QQ+ in top row
    
    # Scenario 1: Stay with trips in top
    top_trips = [cards["AH"], cards["AD"], cards["AC"]]
    middle_normal = [cards["KH"], cards["QH"], cards["9H"], cards["8C"], cards["7H"]]
    bottom_normal = [cards["KD"], cards["QD"], cards["9D"], cards["9C"], cards["7D"]]
    
    can_stay = manager.check_stay_qualification(top_trips, middle_normal, bottom_normal)
    print(f"Trips in top: {can_stay} (should be True)")
    
    # Scenario 2: Stay with QQ in top
    top_qq = [cards["QH"], cards["QD"], cards["KC"]]
    middle_fh = [cards["KH"], cards["KD"], cards["KS"], cards["7H"], cards["7D"]]
    
    can_stay = manager.check_stay_qualification(top_qq, middle_fh, bottom_normal)
    print(f"QQ in top: {can_stay} (should be True)")
    
    # Scenario 3: Cannot stay - strong bottom but weak top
    top_weak = [cards["JH"], cards["JD"], cards["KC"]]
    bottom_quads = [cards["9H"], cards["9D"], cards["9C"], cards["9S"], cards["8C"]]
    
    can_stay = manager.check_stay_qualification(top_weak, middle_normal, bottom_quads)
    print(f"Quads in bottom but weak top: {can_stay} (should be False)")
    
    # Scenario 4: Cannot stay - no QQ+ in top
    can_stay = manager.check_stay_qualification(top_weak, middle_normal, bottom_normal)
    print(f"No qualifying hands: {can_stay} (should be False)")


def test_fantasy_placement_validation():
    """Test Fantasy Land card placement validation."""
    print("\n=== Testing Fantasy Land Placement ===")
    
    manager = PineappleFantasyLandManager()
    
    # Create 14 cards for Fantasy Land
    dealt = []
    for rank in [Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK, Rank.TEN, 
                 Rank.NINE, Rank.EIGHT, Rank.SEVEN, Rank.SIX, Rank.FIVE,
                 Rank.FOUR, Rank.THREE, Rank.TWO]:
        dealt.append(Card(Suit.HEARTS, rank))
    dealt.append(Card(Suit.SPADES, Rank.ACE))  # 14th card
    
    # Valid placement (13 from 14)
    placed = dealt[:13]  # Place first 13, discard last
    valid, error = manager.validate_fantasy_placement(placed, dealt)
    print(f"Valid placement: {valid}, error: {error}")
    
    # Invalid - too few cards
    placed_few = dealt[:12]
    valid, error = manager.validate_fantasy_placement(placed_few, dealt)
    print(f"Too few cards: {valid}, error: {error}")
    
    # Invalid - card not from dealt
    placed_wrong = dealt[:12] + [Card(Suit.CLUBS, Rank.KING)]
    valid, error = manager.validate_fantasy_placement(placed_wrong, dealt)
    print(f"Wrong card: {valid}, error: {error}")


def main():
    """Run all Fantasy Land tests."""
    print("=" * 60)
    print("Fantasy Land MVP Demo")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    test_fantasy_land_entry()
    test_fantasy_land_state()
    test_stay_qualification()
    test_fantasy_placement_validation()
    
    print("\n" + "=" * 60)
    print("Fantasy Land MVP tests completed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()