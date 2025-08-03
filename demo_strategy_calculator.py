"""
Demo script for Strategy Calculator (TASK-009).

Shows how the strategy calculator works with game trees to find optimal plays.
Includes performance metrics and confidence intervals.
"""

import time
from typing import List

from src.domain.value_objects.card import Card, Rank, Suit
from src.domain.value_objects.hand import Hand
from src.domain.services.strategy_calculator import StrategyCalculator
from src.domain.services.game_tree_builder import GameTreeBuilder
from src.domain.services.pineapple_evaluator import PineappleHandEvaluator


def create_sample_deck() -> List[Card]:
    """Create a full deck of cards."""
    suit_map = {
        'hearts': Suit.HEARTS,
        'diamonds': Suit.DIAMONDS,
        'clubs': Suit.CLUBS,
        'spades': Suit.SPADES
    }
    
    rank_map = {
        '2': Rank.TWO, '3': Rank.THREE, '4': Rank.FOUR, '5': Rank.FIVE,
        '6': Rank.SIX, '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
        'T': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN, 'K': Rank.KING, 'A': Rank.ACE
    }
    
    deck = []
    for suit_name, suit in suit_map.items():
        for rank_name, rank in rank_map.items():
            deck.append(Card(suit=suit, rank=rank))
    
    return deck


def demo_basic_strategy_calculation():
    """Demo basic strategy calculation."""
    print("=== Basic Strategy Calculation Demo ===\n")
    
    # Create services
    evaluator = PineappleHandEvaluator()
    tree_builder = GameTreeBuilder(evaluator)
    calculator = StrategyCalculator(tree_builder, evaluator)
    
    # Create a mid-game position
    hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN), Card(Suit.DIAMONDS, Rank.QUEEN)],  # QQ in top (FL potential)
        middle=[Card(Suit.CLUBS, Rank.EIGHT), Card(Suit.CLUBS, Rank.NINE), Card(Suit.CLUBS, Rank.TEN)],  # Straight draw
        bottom=[Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.KING)],  # Big cards
        hand=[]
    )
    
    # Create remaining deck (remove cards already placed)
    placed_cards = hand.get_all_placed_cards()
    full_deck = create_sample_deck()
    remaining_deck = [card for card in full_deck if card not in placed_cards]
    
    print("Current Position:")
    print(f"Top:    {[str(c) for c in hand.top_row]}")
    print(f"Middle: {[str(c) for c in hand.middle_row]}")
    print(f"Bottom: {[str(c) for c in hand.bottom_row]}")
    print(f"Cards placed: {len(placed_cards)}")
    print(f"Remaining deck size: {len(remaining_deck)}")
    print()
    
    # Calculate optimal strategy
    print("Calculating optimal strategy...")
    start_time = time.time()
    
    # Debug: Show tree builder info before
    print(f"Tree nodes before: {len(calculator.tree_builder.nodes)}")
    
    strategy = calculator.calculate_optimal_strategy(
        current_hand=hand,
        remaining_deck=remaining_deck[:20],  # Use subset for faster demo
        max_depth=2  # Look 2 streets ahead
    )
    
    calc_time = (time.time() - start_time) * 1000
    print(f"Calculation completed in {calc_time:.1f}ms")
    print(f"Tree nodes after: {len(calculator.tree_builder.nodes)}")
    print(f"Tree actions: {len(calculator.tree_builder.actions)}")
    print()
    
    # Display results
    print("Strategy Recommendation:")
    print(f"- {strategy}")
    print(f"- Expected Value: {strategy.expected_value.value:.2f}")
    print(f"- Confidence: {strategy.confidence:.1%}")
    print(f"- Calculation Method: {strategy.calculation_method}")
    
    if strategy.primary_action:
        action = strategy.primary_action
        print(f"\nRecommended Action:")
        print(f"- Place: {[str(c) for c in action.cards_to_place]}")
        print(f"- Discard: {action.card_to_discard}")
        print(f"- Action EV: {action.expected_value:.2f}")
    
    # Show tree statistics
    if strategy.tree_stats:
        print(f"\nTree Statistics:")
        for key, value in strategy.tree_stats.items():
            print(f"- {key}: {value}")
    
    # Show performance stats
    perf_stats = calculator.get_performance_stats()
    print(f"\nPerformance Metrics:")
    print(f"- Cache hit rate: {perf_stats['cache_hit_rate']:.1%}")
    print(f"- Nodes evaluated: {perf_stats['nodes_evaluated']}")
    print(f"- Tree nodes: {perf_stats['tree_nodes']}")


def demo_ev_calculation_with_confidence():
    """Demo EV calculation with confidence intervals."""
    print("\n\n=== EV Calculation with Confidence Intervals ===\n")
    
    # Create services
    evaluator = PineappleHandEvaluator()
    tree_builder = GameTreeBuilder(evaluator)
    calculator = StrategyCalculator(tree_builder, evaluator)
    
    # Create an early game position
    hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.ACE)],
        middle=[Card(Suit.HEARTS, Rank.KING), Card(Suit.HEARTS, Rank.QUEEN)],
        bottom=[Card(Suit.SPADES, Rank.JACK), Card(Suit.SPADES, Rank.TEN)],
        hand=[]
    )
    
    # Create remaining deck
    placed_cards = hand.get_all_placed_cards()
    full_deck = create_sample_deck()
    remaining_deck = [card for card in full_deck if card not in placed_cards]
    
    print("Current Position:")
    print(f"Top:    {[str(c) for c in hand.top_row]}")
    print(f"Middle: {[str(c) for c in hand.middle_row]}")
    print(f"Bottom: {[str(c) for c in hand.bottom_row]}")
    print()
    
    # Calculate EV with different sample sizes
    sample_sizes = [10, 30, 50]
    
    for samples in sample_sizes:
        print(f"\nCalculating EV with {samples} Monte Carlo samples...")
        start_time = time.time()
        
        mean_ev, lower_bound, upper_bound = calculator.calculate_ev_range(
            current_hand=hand,
            remaining_deck=remaining_deck[:30],  # Use subset
            iterations=samples
        )
        
        calc_time = (time.time() - start_time) * 1000
        
        print(f"- Mean EV: {mean_ev:.2f}")
        print(f"- 95% Confidence Interval: [{lower_bound:.2f}, {upper_bound:.2f}]")
        print(f"- Interval width: {upper_bound - lower_bound:.2f}")
        print(f"- Calculation time: {calc_time:.1f}ms")
        
        # Clear caches between runs
        calculator.clear_caches()


def demo_position_evaluation_comparison():
    """Demo comparing different positions."""
    print("\n\n=== Position Evaluation Comparison ===\n")
    
    # Create services
    evaluator = PineappleHandEvaluator()
    tree_builder = GameTreeBuilder(evaluator)
    calculator = StrategyCalculator(tree_builder, evaluator)
    
    # Position 1: Safe balanced position
    safe_hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.NINE), Card(Suit.DIAMONDS, Rank.NINE)],
        middle=[Card(Suit.CLUBS, Rank.JACK), Card(Suit.SPADES, Rank.JACK), Card(Suit.HEARTS, Rank.TEN)],
        bottom=[Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.KING), Card(Suit.SPADES, Rank.QUEEN)],
        hand=[]
    )
    
    # Position 2: Risky but high-reward position
    risky_hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.KING), Card(Suit.DIAMONDS, Rank.KING)],  # Strong top
        middle=[Card(Suit.CLUBS, Rank.QUEEN), Card(Suit.SPADES, Rank.QUEEN)],  # Also strong - risky!
        bottom=[Card(Suit.SPADES, Rank.ACE), Card(Suit.DIAMONDS, Rank.ACE)],  # Very strong
        hand=[]
    )
    
    # Position 3: Fantasy land position
    fl_hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN), Card(Suit.DIAMONDS, Rank.QUEEN), Card(Suit.CLUBS, Rank.THREE)],  # QQ - FL qualified
        middle=[Card(Suit.CLUBS, Rank.EIGHT), Card(Suit.SPADES, Rank.EIGHT), Card(Suit.HEARTS, Rank.SEVEN), Card(Suit.DIAMONDS, Rank.SIX), Card(Suit.CLUBS, Rank.FIVE)],
        bottom=[Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.KING), Card(Suit.SPADES, Rank.JACK), Card(Suit.SPADES, Rank.TEN), Card(Suit.SPADES, Rank.NINE)],  # Flush
        hand=[]
    )
    
    positions = [
        ("Safe Balanced", safe_hand),
        ("High Risk/Reward", risky_hand),
        ("Fantasy Land", fl_hand)
    ]
    
    remaining_deck = create_sample_deck()[:30]  # Use same deck subset for all
    
    print("Comparing different positions:\n")
    
    for name, hand in positions:
        print(f"{name} Position:")
        print(f"Top:    {[str(c) for c in hand.top_row]}")
        print(f"Middle: {[str(c) for c in hand.middle_row]}")
        print(f"Bottom: {[str(c) for c in hand.bottom_row]}")
        
        # Calculate strategy
        strategy = calculator.calculate_optimal_strategy(
            current_hand=hand,
            remaining_deck=remaining_deck,
            max_depth=1  # Shallow for demo
        )
        
        print(f"Expected Value: {strategy.expected_value.value:.2f}")
        print(f"Tree nodes explored: {len(calculator.tree_builder.nodes)}")
        print()
        
        # Clear for next calculation
        calculator.clear_caches()
        calculator.tree_builder.nodes.clear()
        calculator.tree_builder.actions.clear()


def main():
    """Run all demos."""
    print("OFC Strategy Calculator Demo (TASK-009)")
    print("=" * 50)
    print()
    
    # Run demos
    demo_basic_strategy_calculation()
    demo_ev_calculation_with_confidence()
    demo_position_evaluation_comparison()
    
    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    main()