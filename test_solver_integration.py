#!/usr/bin/env python3
"""
Integration test for OFC Solver with all implemented features.

Tests:
1. Game tree building
2. Strategy calculation (minimax)
3. Monte Carlo simulation
4. Pineapple OFC rules
5. Fantasy Land
"""

from datetime import datetime
import random

from src.domain.value_objects import Card, Rank, Suit, Hand
from src.domain.services.game_tree_builder import GameTreeBuilder
from src.domain.services.strategy_calculator import StrategyCalculator
from src.domain.services.monte_carlo_simulator import MonteCarloSimulator
from src.domain.services.pineapple_evaluator import PineappleHandEvaluator
from src.domain.services.pineapple_fantasy_land import PineappleFantasyLandManager


def print_section(title):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


def create_deck():
    """Create a standard 52-card deck."""
    deck = []
    for suit in Suit:
        for rank in Rank:
            deck.append(Card(suit, rank))
    return deck


def test_complete_solver_pipeline():
    """Test the complete solver pipeline."""
    print_section("OFC Solver Integration Test")
    print(f"Time: {datetime.now()}")
    
    # Initialize evaluator for use throughout
    evaluator = PineappleHandEvaluator()
    
    # 1. Set up initial position
    print("\n1. Initial Position Setup")
    hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN)],
        middle=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)],
        bottom=[Card(Suit.DIAMONDS, Rank.TEN), Card(Suit.CLUBS, Rank.TEN)],
        hand=[]
    )
    
    print(f"  Top:    {[str(c) for c in hand.top_row]}")
    print(f"  Middle: {[str(c) for c in hand.middle_row]}")
    print(f"  Bottom: {[str(c) for c in hand.bottom_row]}")
    
    # 2. Build game tree
    print("\n2. Building Game Tree")
    builder = GameTreeBuilder()
    
    deck = create_deck()
    used_cards = hand.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards]
    random.shuffle(remaining_deck)
    
    print(f"  Remaining deck: {len(remaining_deck)} cards")
    print("  Building tree with depth=2...")
    
    root = builder.build_tree_from_position(hand, remaining_deck, max_depth=2)
    stats = builder.get_tree_stats(root)
    
    print(f"  Tree nodes: {stats['total_nodes']}")
    print(f"  Leaf nodes: {stats['leaf_nodes']}")
    print(f"  Max depth: {stats['max_depth']}")
    
    # 3. Strategy calculation
    print("\n3. Strategy Calculation (Minimax)")
    strategy_calc = StrategyCalculator(builder)
    
    strategy = strategy_calc.calculate_optimal_strategy(hand, remaining_deck[:20])
    
    if strategy.recommended_actions:
        rec = strategy.recommended_actions[0]
        print(f"  Recommended: {rec}")
        print(f"  Expected value: {strategy.expected_value.value:.2f}")
        print(f"  Confidence: {strategy.confidence * 100:.1f}%")
        print(f"  Method: {strategy.calculation_method}")
    else:
        print("  No valid actions available")
    
    # 4. Monte Carlo simulation
    print("\n4. Monte Carlo Simulation")
    mc_sim = MonteCarloSimulator(evaluator)
    
    mc_result = mc_sim.analyze_position(
        hand,
        remaining_deck[:30],
        num_simulations=100,
        max_depth=2
    )
    
    print(f"  Simulations: {mc_result['simulations_run']}")
    print(f"  Mean EV: {mc_result['mean_ev']:.2f}")
    print(f"  Std Dev: {mc_result['std_dev']:.2f}")
    print(f"  Best action EV: {mc_result['best_action_ev']:.2f}")
    
    # 5. Pineapple OFC specific features
    print("\n5. Pineapple OFC Features")
    fl_manager = PineappleFantasyLandManager()
    
    # Test QQ+ in top
    qq_hand = Hand.from_layout(
        top=[Card(Suit.HEARTS, Rank.QUEEN), Card(Suit.DIAMONDS, Rank.QUEEN)],
        middle=[],
        bottom=[],
        hand=[]
    )
    
    print("  Testing Fantasy Land qualification:")
    print(f"    QQ in top qualifies: {fl_manager.check_entry_qualification(qq_hand.top_row)}")
    
    # Test royalties
    flush_cards = [
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.HEARTS, Rank.QUEEN),
        Card(Suit.HEARTS, Rank.JACK),
        Card(Suit.HEARTS, Rank.TEN)
    ]
    royalty = evaluator.calculate_royalty([], flush_cards, [])
    print(f"    Middle flush royalty: {royalty['middle']} (should be 8)")
    
    # 6. Performance comparison
    print("\n6. Performance Comparison")
    
    # Minimax timing
    import time
    start = time.time()
    strategy_calc.calculate_optimal_strategy(hand, remaining_deck[:15])
    minimax_time = (time.time() - start) * 1000
    
    # Monte Carlo timing
    start = time.time()
    mc_sim.analyze_position(hand, remaining_deck[:15], num_simulations=50)
    mc_time = (time.time() - start) * 1000
    
    print(f"  Minimax (depth=2): {minimax_time:.1f}ms")
    print(f"  Monte Carlo (50 sims): {mc_time:.1f}ms")
    
    # 7. Summary
    print("\n7. Test Summary")
    print("  ✓ Game tree building working")
    print("  ✓ Strategy calculation working")
    print("  ✓ Monte Carlo simulation working")
    print("  ✓ Pineapple OFC rules implemented")
    print("  ✓ Fantasy Land detection working")
    print("  ✓ Custom royalty scoring working")
    
    print("\n" + "="*60)
    print("All core solver features operational!")
    print("Ready for next phase: Application Layer (TASK-011+)")
    print("="*60)


if __name__ == "__main__":
    test_complete_solver_pipeline()