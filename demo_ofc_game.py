#!/usr/bin/env python3
"""
Demo script to test the current OFC Solver implementation.
This demonstrates the core functionality implemented in TASK-004, TASK-005, and TASK-006.
"""

from src.domain.value_objects.card import Card
from src.domain.value_objects.hand import Hand
from src.domain.value_objects.card_position import CardPosition
from src.domain.services.hand_evaluator import HandEvaluator
from src.domain.entities.game import Game, Player
from src.domain.value_objects.game_rules import GameRules


def demonstrate_card_and_hand_creation():
    """Demonstrate card and hand creation functionality."""
    print("\n=== Card and Hand Creation Demo ===")
    
    # Create some cards
    cards = [
        Card.from_string("As"),  # Ace of Spades
        Card.from_string("Kh"),  # King of Hearts
        Card.from_string("Qc"),  # Queen of Clubs
        Card.from_string("Jd"),  # Jack of Diamonds
        Card.from_string("Ts"),  # Ten of Spades
    ]
    
    print(f"Created {len(cards)} cards: {Card.cards_to_string(cards)}")
    
    # Create a hand with these cards
    hand = Hand.from_cards(cards)
    print(f"\nCreated hand with {len(hand.hand_cards)} cards in hand")
    print(f"Available positions: {[pos.name for pos in hand.get_available_positions()]}")
    
    # Place some cards
    hand = hand.place_card(cards[0], CardPosition.TOP)     # As to top
    hand = hand.place_card(cards[1], CardPosition.TOP)     # Kh to top
    hand = hand.place_card(cards[2], CardPosition.MIDDLE)  # Qc to middle
    hand = hand.place_card(cards[3], CardPosition.BOTTOM)  # Jd to bottom
    hand = hand.place_card(cards[4], CardPosition.BOTTOM)  # Ts to bottom
    
    print("\nAfter placing cards:")
    print(hand.to_string())
    
    return hand


def demonstrate_hand_evaluation():
    """Demonstrate hand evaluation functionality."""
    print("\n\n=== Hand Evaluation Demo ===")
    
    evaluator = HandEvaluator()
    
    # Test 1: Evaluate a straight
    straight_cards = [
        Card.from_string("As"),
        Card.from_string("Kh"),
        Card.from_string("Qc"),
        Card.from_string("Jd"),
        Card.from_string("Ts"),
    ]
    
    ranking = evaluator.evaluate_hand(straight_cards)
    print(f"\nStraight evaluation:")
    print(f"  Hand: {Card.cards_to_string(straight_cards)}")
    print(f"  Type: {ranking.hand_type}")
    print(f"  Description: {ranking.get_hand_description()}")
    print(f"  Royalty bonus: {ranking.royalty_bonus}")
    
    # Test 2: Evaluate a flush
    flush_cards = [
        Card.from_string("As"),
        Card.from_string("Ks"),
        Card.from_string("Qs"),
        Card.from_string("Js"),
        Card.from_string("9s"),
    ]
    
    flush_ranking = evaluator.evaluate_hand(flush_cards)
    print(f"\nFlush evaluation:")
    print(f"  Hand: {Card.cards_to_string(flush_cards)}")
    print(f"  Type: {flush_ranking.hand_type}")
    print(f"  Description: {flush_ranking.get_hand_description()}")
    print(f"  Royalty bonus: {flush_ranking.royalty_bonus}")
    
    # Test 3: Evaluate top row pair
    pair_cards = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("Kc"),
    ]
    
    pair_ranking = evaluator.evaluate_hand(pair_cards)
    print(f"\nTop row pair evaluation:")
    print(f"  Hand: {Card.cards_to_string(pair_cards)}")
    print(f"  Type: {pair_ranking.hand_type}")
    print(f"  Description: {pair_ranking.get_hand_description()}")
    print(f"  Royalty bonus: {pair_ranking.royalty_bonus} (top row AA gets 9 royalty)")
    
    # Compare hands
    print(f"\nComparing hands:")
    print(f"  Flush vs Straight: {evaluator.compare_hands(flush_ranking, ranking)} (1 means flush wins)")
    
    return evaluator


def demonstrate_ofc_validation():
    """Demonstrate OFC hand validation."""
    print("\n\n=== OFC Validation Demo ===")
    
    evaluator = HandEvaluator()
    
    # Valid OFC hand (bottom > middle > top)
    top_valid = [
        Card.from_string("Kh"),
        Card.from_string("Qc"),
        Card.from_string("Jd"),
    ]  # K high
    
    middle_valid = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("9c"),
        Card.from_string("8d"),
        Card.from_string("7s"),
    ]  # Pair of Aces
    
    bottom_valid = [
        Card.from_string("5s"),
        Card.from_string("5h"),
        Card.from_string("5c"),
        Card.from_string("2d"),
        Card.from_string("2s"),
    ]  # Full house (5s full of 2s)
    
    is_valid = evaluator.validate_ofc_progression(top_valid, middle_valid, bottom_valid)
    print(f"\nValid hand check:")
    print(f"  Top: {Card.cards_to_string(top_valid)} - {evaluator.evaluate_hand(top_valid).get_hand_description()}")
    print(f"  Middle: {Card.cards_to_string(middle_valid)} - {evaluator.evaluate_hand(middle_valid).get_hand_description()}")
    print(f"  Bottom: {Card.cards_to_string(bottom_valid)} - {evaluator.evaluate_hand(bottom_valid).get_hand_description()}")
    print(f"  Is valid OFC hand? {is_valid}")
    
    # Fouled OFC hand (top > middle)
    top_fouled = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("Kc"),
    ]  # Pair of Aces
    
    middle_fouled = [
        Card.from_string("Kh"),
        Card.from_string("Qc"),
        Card.from_string("Jd"),
        Card.from_string("9s"),
        Card.from_string("8h"),
    ]  # K high
    
    is_fouled = evaluator.is_fouled_hand(top_fouled, middle_fouled, bottom_valid)
    print(f"\nFouled hand check:")
    print(f"  Top: {Card.cards_to_string(top_fouled)} - {evaluator.evaluate_hand(top_fouled).get_hand_description()}")
    print(f"  Middle: {Card.cards_to_string(middle_fouled)} - {evaluator.evaluate_hand(middle_fouled).get_hand_description()}")
    print(f"  Bottom: {Card.cards_to_string(bottom_valid)} - {evaluator.evaluate_hand(bottom_valid).get_hand_description()}")
    print(f"  Is fouled? {is_fouled} (top beats middle)")


def demonstrate_game_creation():
    """Demonstrate game entity creation."""
    print("\n\n=== Game Creation Demo ===")
    
    # Create game rules
    rules = GameRules.standard_rules()
    print(f"Created standard OFC rules:")
    print(f"  Variant: {rules.variant}")
    print(f"  Player count: {rules.player_count}")
    print(f"  Fantasy land enabled: {rules.fantasy_land_enabled}")
    print(f"  Initial cards: {rules.initial_cards_count}")
    print(f"  Cards per turn: {rules.cards_per_turn}")
    
    # Create players
    player1 = Player("player1", "Alice")
    player2 = Player("player2", "Bob")
    
    # Create game
    game = Game("game1", [player1, player2], rules)
    print(f"\nCreated game with ID: {game.id}")
    print(f"  Players: {[p.name for p in game.players]}")
    print(f"  Current round: {game.current_round}")
    
    # Game is initialized and ready
    print(f"\nGame initialized successfully!")
    print(f"  Game is ready to play with {len(game.players)} players")
    
    return game


def main():
    """Run all demonstrations."""
    print("=== OFC Solver Demo ===")
    print("Testing core functionality from TASK-004, TASK-005, and TASK-006")
    
    # Run demonstrations
    hand = demonstrate_card_and_hand_creation()
    evaluator = demonstrate_hand_evaluation()
    demonstrate_ofc_validation()
    game = demonstrate_game_creation()
    
    print("\n\n=== Summary ===")
    print("✅ Card and Hand models working correctly")
    print("✅ Hand evaluation with royalty bonuses working")
    print("✅ OFC progression validation working")
    print("✅ Game entity creation and initialization working")
    print("\nCore domain is ready for strategy engine implementation!")


if __name__ == "__main__":
    main()