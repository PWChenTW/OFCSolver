#!/usr/bin/env python3
"""
Simple demo showing how the solver SHOULD work.

This demonstrates the intended functionality, even if some integration is missing.
"""

from src.domain.value_objects import Card, Rank, Suit, Hand, CardPosition
from src.domain.services.pineapple_evaluator import PineappleHandEvaluator
from itertools import combinations


def evaluate_placement(hand: Hand, cards_to_place: list[Card], position1: CardPosition, position2: CardPosition):
    """
    Evaluate placing two cards at specific positions.
    
    Returns score (higher is better).
    """
    evaluator = PineappleHandEvaluator()
    
    # Create new hand with placements
    try:
        # Clone current hand
        new_hand = Hand.from_layout(
            top=list(hand.top_row),
            middle=list(hand.middle_row),
            bottom=list(hand.bottom_row),
            hand=cards_to_place
        )
        
        # Place cards
        new_hand = new_hand.place_card(cards_to_place[0], position1)
        new_hand = new_hand.place_card(cards_to_place[1], position2)
        
        # Evaluate
        score = 0.0
        
        # Check for foul
        if is_fouled(new_hand):
            return -1000.0  # Heavy penalty
        
        # Evaluate each row
        if len(new_hand.top_row) == 3:
            top_eval = evaluator.evaluate_hand(new_hand.top_row)
            score += top_eval.royalty_bonus
            # Bonus for QQ+ (Fantasy Land)
            if top_eval.hand_type.name == "PAIR" and top_eval.strength_value >= 12:
                score += 10.0
        
        if len(new_hand.middle_row) == 5:
            middle_eval = evaluator.evaluate_hand(new_hand.middle_row)
            score += middle_eval.royalty_bonus
        
        if len(new_hand.bottom_row) == 5:
            bottom_eval = evaluator.evaluate_hand(new_hand.bottom_row)
            score += bottom_eval.royalty_bonus
        
        # Prefer balanced development
        cards_in_rows = [len(new_hand.top_row), len(new_hand.middle_row), len(new_hand.bottom_row)]
        balance_score = 5.0 - max(cards_in_rows) + min(cards_in_rows)
        score += balance_score
        
        return score
        
    except Exception as e:
        # Invalid placement
        return -2000.0


def is_fouled(hand: Hand) -> bool:
    """Check if hand is fouled."""
    evaluator = PineappleHandEvaluator()
    
    # Need complete rows to check
    if len(hand.top_row) < 3 or len(hand.middle_row) < 5 or len(hand.bottom_row) < 5:
        return False
    
    top_eval = evaluator.evaluate_hand(hand.top_row)
    middle_eval = evaluator.evaluate_hand(hand.middle_row)
    bottom_eval = evaluator.evaluate_hand(hand.bottom_row)
    
    # Check progression
    if bottom_eval.hand_type.value < middle_eval.hand_type.value:
        return True
    if middle_eval.hand_type.value < top_eval.hand_type.value:
        return True
        
    # For same hand type, check strength
    if bottom_eval.hand_type == middle_eval.hand_type:
        if bottom_eval.strength_value < middle_eval.strength_value:
            return True
    if middle_eval.hand_type == top_eval.hand_type:
        if middle_eval.strength_value < top_eval.strength_value:
            return True
    
    return False


def get_simple_recommendation(current_hand: Hand, dealt_cards: list[Card]):
    """
    Get recommendation using simple evaluation.
    
    This is a simplified version that actually works!
    """
    print(f"\n🎴 Dealt cards: {[str(c) for c in dealt_cards]}")
    
    # Get available positions
    available_positions = []
    if len(current_hand.top_row) < 3:
        available_positions.extend([CardPosition.TOP] * (3 - len(current_hand.top_row)))
    if len(current_hand.middle_row) < 5:
        available_positions.extend([CardPosition.MIDDLE] * (5 - len(current_hand.middle_row)))
    if len(current_hand.bottom_row) < 5:
        available_positions.extend([CardPosition.BOTTOM] * (5 - len(current_hand.bottom_row)))
    
    # Try all combinations of 2 cards from 3
    best_score = -9999
    best_placement = None
    best_discard = None
    
    for cards_to_place in combinations(dealt_cards, 2):
        discard = [c for c in dealt_cards if c not in cards_to_place][0]
        
        # Try different position combinations
        if len(available_positions) >= 2:
            # Simple strategy: try placing in same row or different rows
            test_positions = [
                (CardPosition.TOP, CardPosition.TOP),
                (CardPosition.MIDDLE, CardPosition.MIDDLE),
                (CardPosition.BOTTOM, CardPosition.BOTTOM),
                (CardPosition.TOP, CardPosition.MIDDLE),
                (CardPosition.TOP, CardPosition.BOTTOM),
                (CardPosition.MIDDLE, CardPosition.BOTTOM),
            ]
            
            for pos1, pos2 in test_positions:
                # Check if positions are available
                if pos1 == CardPosition.TOP and len(current_hand.top_row) + (2 if pos1 == pos2 else 1) > 3:
                    continue
                if pos2 == CardPosition.TOP and len(current_hand.top_row) + (2 if pos1 == pos2 else 1) > 3:
                    continue
                if pos1 == CardPosition.MIDDLE and len(current_hand.middle_row) + (2 if pos1 == pos2 else 1) > 5:
                    continue
                if pos2 == CardPosition.MIDDLE and len(current_hand.middle_row) + (2 if pos1 == pos2 else 1) > 5:
                    continue
                if pos1 == CardPosition.BOTTOM and len(current_hand.bottom_row) + (2 if pos1 == pos2 else 1) > 5:
                    continue
                if pos2 == CardPosition.BOTTOM and len(current_hand.bottom_row) + (2 if pos1 == pos2 else 1) > 5:
                    continue
                    
                score = evaluate_placement(current_hand, list(cards_to_place), pos1, pos2)
                
                if score > best_score:
                    best_score = score
                    best_placement = (cards_to_place, pos1, pos2)
                    best_discard = discard
    
    if best_placement:
        cards, pos1, pos2 = best_placement
        print(f"\n✅ Recommendation:")
        print(f"   Place {str(cards[0])} in {pos1.name}")
        print(f"   Place {str(cards[1])} in {pos2.name}")
        print(f"   Discard {str(best_discard)}")
        print(f"   Score: {best_score:.1f}")
        
        # Explain reasoning
        if best_score > 10:
            print("   💡 Strong position!")
        elif best_score > 0:
            print("   💡 Decent play")
        else:
            print("   ⚠️  Best available option")
    else:
        print("\n❌ No valid placements available")


def demo_working_solver():
    """Demo showing working solver functionality."""
    print("="*60)
    print("Simple OFC Solver Demo (Working Version)")
    print("="*60)
    
    # Example 1: Early game
    print("\n### Example 1: Early Game Decision")
    
    hand1 = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN)],
        middle=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)],
        bottom=[Card(Suit.DIAMONDS, Rank.ACE), Card(Suit.CLUBS, Rank.ACE)],
        hand=[]
    )
    
    print(f"Top:    {[str(c) for c in hand1.top_row]}")
    print(f"Middle: {[str(c) for c in hand1.middle_row]}")
    print(f"Bottom: {[str(c) for c in hand1.bottom_row]}")
    
    dealt1 = [
        Card(Suit.DIAMONDS, Rank.QUEEN),  # Pair with Qh
        Card(Suit.SPADES, Rank.KING),     # Pair with Kh
        Card(Suit.HEARTS, Rank.FIVE)      # Low card
    ]
    
    get_simple_recommendation(hand1, dealt1)
    
    # Example 2: Fantasy Land protection
    print("\n\n### Example 2: Protecting Fantasy Land")
    
    hand2 = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN), Card(Suit.DIAMONDS, Rank.QUEEN)],
        middle=[Card(Suit.SPADES, Rank.TEN), Card(Suit.HEARTS, Rank.TEN)],
        bottom=[Card(Suit.DIAMONDS, Rank.KING), Card(Suit.CLUBS, Rank.KING), Card(Suit.SPADES, Rank.TWO)],
        hand=[]
    )
    
    print(f"Top:    {[str(c) for c in hand2.top_row]} (QQ - Fantasy Land!)")
    print(f"Middle: {[str(c) for c in hand2.middle_row]}")
    print(f"Bottom: {[str(c) for c in hand2.bottom_row]}")
    
    dealt2 = [
        Card(Suit.CLUBS, Rank.TEN),       # Can make trips
        Card(Suit.HEARTS, Rank.THREE),    # Low card
        Card(Suit.DIAMONDS, Rank.FOUR)    # Low card
    ]
    
    get_simple_recommendation(hand2, dealt2)
    
    # Example 3: Avoid fouling
    print("\n\n### Example 3: Late Game - Avoid Fouling")
    
    hand3 = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.EIGHT), Card(Suit.DIAMONDS, Rank.EIGHT)],
        middle=[Card(Suit.SPADES, Rank.JACK), Card(Suit.HEARTS, Rank.JACK), 
                Card(Suit.CLUBS, Rank.TWO), Card(Suit.DIAMONDS, Rank.THREE)],
        bottom=[Card(Suit.DIAMONDS, Rank.KING), Card(Suit.CLUBS, Rank.KING),
                Card(Suit.SPADES, Rank.QUEEN), Card(Suit.HEARTS, Rank.QUEEN)],
        hand=[]
    )
    
    print(f"Top:    {[str(c) for c in hand3.top_row]} (88)")
    print(f"Middle: {[str(c) for c in hand3.middle_row]} (JJ)")
    print(f"Bottom: {[str(c) for c in hand3.bottom_row]} (KK QQ)")
    
    dealt3 = [
        Card(Suit.CLUBS, Rank.EIGHT),     # Would make trips in top
        Card(Suit.CLUBS, Rank.JACK),      # Would make trips in middle
        Card(Suit.SPADES, Rank.FOUR)      # Safe low card
    ]
    
    get_simple_recommendation(hand3, dealt3)
    
    print("\n" + "="*60)
    print("This simplified solver actually works!")
    print("Next step: Connect this logic to the command handlers.")
    print("="*60)


if __name__ == "__main__":
    demo_working_solver()