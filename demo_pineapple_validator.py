#!/usr/bin/env python3
"""
Demo script for Pineapple OFC Game Validator.

Tests the validator with various Pineapple-specific scenarios:
1. 3-pick-2 validation
2. Initial placement validation
3. Fantasy Land qualification
4. Discard tracking
"""

from datetime import datetime
from uuid import uuid4

from src.domain.value_objects import (
    Card, Rank, Suit, GameRules, Position, Row,
    PineappleAction, InitialPlacement, FantasyLandState
)
from src.domain.entities.game import Game
from src.domain.entities.game.player import Player
from src.domain.services import PineappleGameValidator


def create_sample_cards():
    """Create sample cards for testing."""
    cards = []
    suits = [Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES]
    ranks = [Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK, Rank.TEN,
             Rank.NINE, Rank.EIGHT, Rank.SEVEN, Rank.SIX, Rank.FIVE]
    
    for i, rank in enumerate(ranks):
        cards.append(Card(suits[i % 4], rank))
    
    return cards


def create_test_game():
    """Create a test game with 2 players."""
    rules = GameRules.pineapple_rules()
    
    # Create players
    player1 = Player("player1", "Alice")
    player2 = Player("player2", "Bob")
    
    # Create game with players
    game = Game("test_game", [player1, player2], rules)
    
    return game, player1, player2


def test_pineapple_action_validation():
    """Test 3-pick-2 action validation."""
    print("\n=== Testing Pineapple Action Validation ===")
    
    game, player1, player2 = create_test_game()
    validator = PineappleGameValidator()
    cards = create_sample_cards()
    
    # Valid action
    dealt = cards[:3]  # Deal 3 cards
    action = PineappleAction(
        player_id=player1.id,
        street=1,
        dealt_cards=dealt,
        placements=[
            (cards[0], Position(Row.TOP, 0)),
            (cards[1], Position(Row.MIDDLE, 0)),
        ],
        discarded_card=cards[2]
    )
    
    result = validator.validate_pineapple_action(action, player1, game)
    print(f"Valid action: {result.is_valid} - {result.error_message}")
    
    # Invalid - wrong number of dealt cards
    try:
        bad_action = PineappleAction(
            player_id=player1.id,
            street=1,
            dealt_cards=cards[:2],  # Only 2 cards
            placements=[(cards[0], Position(Row.TOP, 0))],
            discarded_card=cards[1]
        )
        result = validator.validate_pineapple_action(bad_action, player1, game)
        print(f"Wrong dealt count: {result.is_valid} - {result.error_message}")
    except ValueError as e:
        print(f"Wrong dealt count: False - {e}")
    
    # Track discarded card
    validator.track_discarded_card(cards[2])
    print(f"Discarded cards tracked: {validator.get_discard_count()}")


def test_initial_placement_validation():
    """Test initial 5-card placement validation."""
    print("\n=== Testing Initial Placement Validation ===")
    
    game, player1, player2 = create_test_game()
    validator = PineappleGameValidator()
    cards = create_sample_cards()
    
    # Valid initial placement
    placement = InitialPlacement(
        player_id=player1.id,
        placements=[
            (cards[0], Position(Row.TOP, 0)),
            (cards[1], Position(Row.TOP, 1)),
            (cards[2], Position(Row.MIDDLE, 0)),
            (cards[3], Position(Row.BOTTOM, 0)),
            (cards[4], Position(Row.BOTTOM, 1)),
        ]
    )
    
    result = validator.validate_initial_placement(placement, player1, game)
    print(f"Valid placement: {result.is_valid} - {result.error_message}")
    
    # Invalid - duplicate position
    try:
        bad_placement = InitialPlacement(
            player_id=player1.id,
            placements=[
                (cards[0], Position(Row.TOP, 0)),
                (cards[1], Position(Row.TOP, 0)),  # Duplicate position
                (cards[2], Position(Row.MIDDLE, 0)),
                (cards[3], Position(Row.BOTTOM, 0)),
                (cards[4], Position(Row.BOTTOM, 1)),
            ]
        )
        result = validator.validate_initial_placement(bad_placement, player1, game)
        print(f"Duplicate position: {result.is_valid} - {result.error_message}")
    except ValueError as e:
        print(f"Duplicate position: False - {e}")


def test_fantasy_land_validation():
    """Test Fantasy Land entry and stay validation."""
    print("\n=== Testing Fantasy Land Validation ===")
    
    validator = PineappleGameValidator()
    
    # Test just the Fantasy Land manager directly
    print("Testing Fantasy Land manager functions:")
    
    # Test entry with QQ
    qq_cards = [
        Card(Suit.HEARTS, Rank.QUEEN),
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.KING),
    ]
    qualifies = validator._fantasy_land_manager.check_entry_qualification(qq_cards)
    print(f"QQ qualifies for entry: {qualifies}")
    
    # Test stay with trips
    trips_cards = [
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.ACE),
        Card(Suit.CLUBS, Rank.ACE),
    ]
    middle_cards = [
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.SPADES, Rank.KING),
        Card(Suit.SPADES, Rank.QUEEN),
        Card(Suit.SPADES, Rank.JACK),
        Card(Suit.SPADES, Rank.TEN),
    ]
    bottom_cards = [
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.KING),
        Card(Suit.HEARTS, Rank.NINE),
        Card(Suit.DIAMONDS, Rank.NINE),
    ]
    
    can_stay = validator._fantasy_land_manager.check_stay_qualification(
        trips_cards, middle_cards, bottom_cards
    )
    print(f"Trips in top allows staying: {can_stay}")
    
    # Test Fantasy Land state transitions
    player_id = uuid4()
    state = FantasyLandState.create_initial(player_id)
    print(f"\nInitial FL state: active={state.is_active}")
    
    state = state.enter_fantasy_land(current_round=1)
    print(f"After entering FL: active={state.is_active}, count={state.consecutive_count}")
    
    state = state.enter_fantasy_land(current_round=2)
    print(f"After staying in FL: active={state.is_active}, count={state.consecutive_count}")


def test_fantasy_land_placement():
    """Test Fantasy Land card placement validation."""
    print("\n=== Testing Fantasy Land Placement ===")
    
    validator = PineappleGameValidator()
    cards = create_sample_cards()
    
    # Create 14 cards for Fantasy Land
    dealt_cards = []
    for i in range(14):
        rank = list(Rank)[i % 13]
        suit = list(Suit)[i % 4]
        dealt_cards.append(Card(suit, rank))
    
    # Valid placement - 13 from 14
    placed_cards = dealt_cards[:13]
    
    result = validator.validate_fantasy_land_placement(placed_cards, dealt_cards)
    print(f"Valid FL placement: {result.is_valid} - {result.error_message}")
    
    # Invalid - wrong number of cards
    placed_too_many = dealt_cards  # All 14
    
    result = validator.validate_fantasy_land_placement(placed_too_many, dealt_cards)
    print(f"Too many cards: {result.is_valid} - {result.error_message}")


def main():
    """Run all validator tests."""
    print("=" * 60)
    print("Pineapple OFC Validator Demo")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    test_pineapple_action_validation()
    test_initial_placement_validation()
    test_fantasy_land_validation()
    test_fantasy_land_placement()
    
    print("\n" + "=" * 60)
    print("Pineapple Validator tests completed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()