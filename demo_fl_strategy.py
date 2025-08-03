#!/usr/bin/env python3
"""
Demo script for Fantasy Land Strategy Analysis.

Shows how the strategy analyzer helps with:
1. Top row placement decisions
2. FL entry probability calculation
3. Risk assessment
4. Fantasy Land optimal play
"""

from datetime import datetime

from src.domain.value_objects import Card, Rank, Suit
from src.domain.services.fantasy_land_strategy import FantasyLandStrategyAnalyzer


def create_scenario_cards():
    """Create cards for different scenarios."""
    return {
        # High cards for FL potential
        "AH": Card(Suit.HEARTS, Rank.ACE),
        "AD": Card(Suit.DIAMONDS, Rank.ACE),
        "KH": Card(Suit.HEARTS, Rank.KING),
        "KD": Card(Suit.DIAMONDS, Rank.KING),
        "QH": Card(Suit.HEARTS, Rank.QUEEN),
        "QD": Card(Suit.DIAMONDS, Rank.QUEEN),
        "QC": Card(Suit.CLUBS, Rank.QUEEN),
        
        # Middle cards
        "JH": Card(Suit.HEARTS, Rank.JACK),
        "JS": Card(Suit.SPADES, Rank.JACK),
        "TH": Card(Suit.HEARTS, Rank.TEN),
        "TS": Card(Suit.SPADES, Rank.TEN),
        
        # Lower cards
        "9H": Card(Suit.HEARTS, Rank.NINE),
        "9D": Card(Suit.DIAMONDS, Rank.NINE),
        "8C": Card(Suit.CLUBS, Rank.EIGHT),
        "7S": Card(Suit.SPADES, Rank.SEVEN),
    }


def test_top_row_decisions():
    """Test top row placement decisions for FL entry."""
    print("\n=== Top Row Placement Analysis ===")
    
    analyzer = FantasyLandStrategyAnalyzer()
    cards = create_scenario_cards()
    
    # Scenario 1: Empty top row, have a Queen
    print("\nScenario 1: Empty top, considering Q placement")
    current_top = []
    candidate = cards["QH"]
    remaining_streets = 4
    
    analysis = analyzer.analyze_top_row_placement(
        current_top, candidate, remaining_streets
    )
    print(f"FL Probability: {analysis['fl_probability']:.2%}")
    print(f"Foul Risk: {analysis['risk_score']:.2%}")
    print(f"EV Score: {analysis['ev_score']:.2f}")
    print(f"Recommendation: {analysis['recommendation']:.2f} (-1=avoid, 1=strong yes)")
    
    # Scenario 2: Already have one Q
    print("\nScenario 2: Have Q, considering another Q")
    current_top = [cards["QH"]]
    candidate = cards["QD"]
    remaining_streets = 3
    
    analysis = analyzer.analyze_top_row_placement(
        current_top, candidate, remaining_streets
    )
    print(f"FL Probability: {analysis['fl_probability']:.2%}")
    print(f"Foul Risk: {analysis['risk_score']:.2%}")
    print(f"EV Score: {analysis['ev_score']:.2f}")
    print(f"Recommendation: {analysis['recommendation']:.2f}")
    
    # Scenario 3: Late street, risky placement
    print("\nScenario 3: Late street, considering A placement")
    current_top = [cards["JH"], cards["JS"]]
    candidate = cards["AH"]
    remaining_streets = 1
    
    analysis = analyzer.analyze_top_row_placement(
        current_top, candidate, remaining_streets
    )
    print(f"FL Probability: {analysis['fl_probability']:.2%}")
    print(f"Foul Risk: {analysis['risk_score']:.2%}")
    print(f"EV Score: {analysis['ev_score']:.2f}")
    print(f"Recommendation: {analysis['recommendation']:.2f}")


def test_street_priorities():
    """Test priority recommendations for different streets."""
    print("\n=== Street Priority Analysis ===")
    
    analyzer = FantasyLandStrategyAnalyzer()
    
    # Test each street
    for street in range(5):
        current_state = {
            "top": [],
            "middle": [],
            "bottom": [],
        }
        
        priorities = analyzer.calculate_street_priorities(current_state, street)
        print(f"\nStreet {street} priorities:")
        print(f"  Top: {priorities['top']:.1%}")
        print(f"  Middle: {priorities['middle']:.1%}")
        print(f"  Bottom: {priorities['bottom']:.1%}")


def test_fantasy_land_optimization():
    """Test Fantasy Land hand optimization."""
    print("\n=== Fantasy Land Optimization ===")
    
    analyzer = FantasyLandStrategyAnalyzer()
    
    # Create 14 cards for FL
    fl_cards = [
        # Potential trips for staying
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.KING),
        
        # Potential flush
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.SPADES, Rank.QUEEN),
        Card(Suit.SPADES, Rank.JACK),
        Card(Suit.SPADES, Rank.TEN),
        Card(Suit.SPADES, Rank.NINE),
        
        # Other cards
        Card(Suit.HEARTS, Rank.QUEEN),
        Card(Suit.DIAMONDS, Rank.JACK),
        Card(Suit.HEARTS, Rank.TEN),
        Card(Suit.CLUBS, Rank.NINE),
        Card(Suit.DIAMONDS, Rank.EIGHT),
        Card(Suit.HEARTS, Rank.SEVEN),
    ]
    
    recommendation = analyzer.recommend_fantasy_land_play(fl_cards)
    
    print("\nRecommended placement:")
    print(f"Top: {[str(c) for c in recommendation['top']]}")
    print(f"Middle: {[str(c) for c in recommendation['middle']]}")
    print(f"Bottom: {[str(c) for c in recommendation['bottom']]}")
    print(f"Discard: {recommendation['discarded']}")
    print(f"Can stay in FL: {recommendation['can_stay']}")
    print(f"Expected royalties: {recommendation['expected_royalties']} points")


def test_ev_calculations():
    """Test EV calculation examples."""
    print("\n=== EV Calculation Examples ===")
    
    analyzer = FantasyLandStrategyAnalyzer()
    
    # Show the key parameters
    print(f"FL Entry Bonus: {analyzer.FL_ENTRY_BONUS} points")
    print(f"Foul Penalty: {analyzer.FOUL_PENALTY} points")
    print(f"QQ Probability Threshold: {analyzer.QQ_PROBABILITY_THRESHOLD:.1%}")
    
    # Example calculations
    scenarios = [
        ("Conservative", 0.20, 0.10),  # 20% FL, 10% foul
        ("Aggressive", 0.40, 0.30),    # 40% FL, 30% foul
        ("Safe", 0.15, 0.05),          # 15% FL, 5% foul
    ]
    
    print("\nScenario Analysis:")
    for name, fl_prob, foul_risk in scenarios:
        ev = (fl_prob * analyzer.FL_ENTRY_BONUS) - (foul_risk * analyzer.FOUL_PENALTY)
        print(f"{name:12} - FL: {fl_prob:.0%}, Foul: {foul_risk:.0%}, EV: {ev:+.2f}")


def main():
    """Run all strategy analysis demos."""
    print("=" * 60)
    print("Fantasy Land Strategy Analysis Demo")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    test_top_row_decisions()
    test_street_priorities()
    test_fantasy_land_optimization()
    test_ev_calculations()
    
    print("\n" + "=" * 60)
    print("Strategy analysis completed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()