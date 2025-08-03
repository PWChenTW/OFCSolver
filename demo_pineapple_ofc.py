#!/usr/bin/env python3
"""
Demo script for Pineapple OFC functionality.

Tests the Pineapple-specific features:
1. 3-pick-2 card dealing
2. Enhanced middle row royalties
3. Fantasy Land qualification at QQ+
"""

from datetime import datetime
from uuid import uuid4

from src.domain.value_objects import (
    Card, Rank, Suit, GameRules, Position, Row,
    PineappleAction, InitialPlacement
)
from src.domain.services import PineappleHandEvaluator


def create_sample_cards():
    """Create sample cards for testing."""
    return {
        # Top row cards
        "QH": Card(Suit.HEARTS, Rank.QUEEN),
        "QD": Card(Suit.DIAMONDS, Rank.QUEEN),
        "KC": Card(Suit.CLUBS, Rank.KING),
        
        # Middle row cards - flush
        "AS": Card(Suit.SPADES, Rank.ACE),
        "KS": Card(Suit.SPADES, Rank.KING),
        "QS": Card(Suit.SPADES, Rank.QUEEN),
        "JS": Card(Suit.SPADES, Rank.JACK),
        "9S": Card(Suit.SPADES, Rank.NINE),
        
        # Bottom row cards - full house
        "AH": Card(Suit.HEARTS, Rank.ACE),
        "AD": Card(Suit.DIAMONDS, Rank.ACE),
        "AC": Card(Suit.CLUBS, Rank.ACE),
        "KH": Card(Suit.HEARTS, Rank.KING),
        "KD": Card(Suit.DIAMONDS, Rank.KING),
        
        # Extra cards for Pineapple action
        "8C": Card(Suit.CLUBS, Rank.EIGHT),
        "7D": Card(Suit.DIAMONDS, Rank.SEVEN),
        "6H": Card(Suit.HEARTS, Rank.SIX),
    }


def test_pineapple_action():
    """Test Pineapple OFC 3-pick-2 action."""
    print("\n=== Testing Pineapple Action (3-pick-2) ===")
    
    player_id = uuid4()
    cards = create_sample_cards()
    
    # Simulate receiving 3 cards
    dealt = [cards["8C"], cards["7D"], cards["6H"]]
    
    # Player chooses to place 2 and discard 1
    action = PineappleAction(
        player_id=player_id,
        street=1,
        dealt_cards=dealt,
        placements=[
            (cards["8C"], Position(Row.TOP, 2)),
            (cards["7D"], Position(Row.MIDDLE, 0)),
        ],
        discarded_card=cards["6H"]
    )
    
    print(f"Dealt cards: {[f'{c.suit.symbol}{c.rank.symbol}' for c in dealt]}")
    print(f"Placed: {[(str(c), str(pos)) for c, pos in action.placements]}")
    print(f"Discarded: {action.discarded_card}")
    print("✓ Pineapple action created successfully")


def test_pineapple_royalties():
    """Test Pineapple-specific royalty calculations."""
    print("\n=== Testing Pineapple Royalties ===")
    
    evaluator = PineappleHandEvaluator()
    cards = create_sample_cards()
    
    # Test top row - QQ (qualifies for Fantasy Land in Pineapple)
    top_cards = [cards["QH"], cards["QD"], cards["KC"]]
    top_ranking = evaluator.evaluate_hand_with_position(top_cards, "top")
    print(f"\nTop row: {[str(c) for c in top_cards]}")
    print(f"Hand type: {top_ranking.hand_type}")
    print(f"Royalty bonus: {top_ranking.royalty_bonus} points")
    print(f"Fantasy Land qualified: {evaluator.is_fantasy_land_qualifying(top_cards)}")
    
    # Test middle row - flush (8 points in Pineapple vs 4 in standard)
    middle_cards = [cards["AS"], cards["KS"], cards["QS"], cards["JS"], cards["9S"]]
    middle_ranking = evaluator.evaluate_hand_with_position(middle_cards, "middle")
    print(f"\nMiddle row: {[str(c) for c in middle_cards]}")
    print(f"Hand type: {middle_ranking.hand_type}")
    print(f"Royalty bonus: {middle_ranking.royalty_bonus} points (Pineapple bonus)")
    
    # Test bottom row - full house (6 points, same as standard)
    bottom_cards = [cards["AH"], cards["AD"], cards["AC"], cards["KH"], cards["KD"]]
    bottom_ranking = evaluator.evaluate_hand_with_position(bottom_cards, "bottom")
    print(f"\nBottom row: {[str(c) for c in bottom_cards]}")
    print(f"Hand type: {bottom_ranking.hand_type}")
    print(f"Royalty bonus: {bottom_ranking.royalty_bonus} points")


def test_initial_placement():
    """Test initial 5-card placement."""
    print("\n=== Testing Initial Placement (Street 0) ===")
    
    player_id = uuid4()
    cards = create_sample_cards()
    
    # Place initial 5 cards
    initial = InitialPlacement(
        player_id=player_id,
        placements=[
            (cards["QH"], Position(Row.TOP, 0)),
            (cards["QD"], Position(Row.TOP, 1)),
            (cards["AS"], Position(Row.MIDDLE, 0)),
            (cards["AH"], Position(Row.BOTTOM, 0)),
            (cards["AD"], Position(Row.BOTTOM, 1)),
        ]
    )
    
    print(f"Placed {len(initial.placements)} cards:")
    for card, pos in initial.placements:
        print(f"  {card} -> {pos}")
    print("✓ Initial placement created successfully")


def test_game_rules():
    """Test Pineapple game rules configuration."""
    print("\n=== Testing Pineapple Game Rules ===")
    
    # Create Pineapple rules
    rules = GameRules.pineapple_rules()
    
    print(f"Variant: {rules.variant}")
    print(f"Initial cards: {rules.initial_cards_count}")
    print(f"Cards per turn: {rules.cards_per_turn}")
    print(f"Fantasy Land enabled: {rules.supports_fantasy_land}")
    
    # Test tournament rules
    tournament_rules = GameRules.tournament_rules(variant="pineapple")
    print(f"\nTournament variant: {tournament_rules.variant}")
    print(f"Time limit: {tournament_rules.time_limit_seconds}s")
    print(f"Royalty multiplier: {tournament_rules.royalty_multiplier}x")


def main():
    """Run all Pineapple OFC tests."""
    print("=" * 60)
    print("Pineapple OFC Demo")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    test_game_rules()
    test_pineapple_action()
    test_initial_placement()
    test_pineapple_royalties()
    
    print("\n" + "=" * 60)
    print("All Pineapple OFC tests completed successfully! ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()