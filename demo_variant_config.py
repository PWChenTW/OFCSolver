#!/usr/bin/env python3
"""
Demo: Game Variant Configuration System
Shows how to use different rule configurations.
"""

from datetime import datetime
from src.domain.value_objects.game_variant_config import (
    GameVariantConfig,
    PINEAPPLE_STANDARD,
    PINEAPPLE_POKERSTARS,
    STANDARD_OFC
)
from src.domain.services.pineapple_fantasy_land import PineappleFantasyLandManager
from src.domain.value_objects import Card, Rank, Suit


def print_config_details(config: GameVariantConfig):
    """Print configuration details."""
    print(f"\n=== {config.variant_name.upper()} Configuration ===")
    print(f"Initial cards: {config.initial_cards}")
    print(f"Cards per turn: {config.cards_per_turn}")
    print(f"Cards to place: {config.cards_to_place}")
    print(f"FL entry: {config.fl_entry_requirement}")
    print(f"FL stay: {config.fl_stay_requirement}")
    print(f"FL cards dealt: {config.fl_cards_dealt}")
    print(f"Middle flush royalty: {config.royalty_middle.get('flush', 'N/A')} points")


def test_config_with_fl_manager():
    """Test using config with Fantasy Land manager."""
    print("\n=== Testing Config with FL Manager ===")
    
    # Create custom config for a hypothetical platform
    custom_config = GameVariantConfig(
        variant_name="pineapple_custom",
        fl_entry_requirement="QQ+",
        fl_stay_requirement="KK+",  # Stricter stay requirement
        royalty_middle={
            "trips": 2,
            "straight": 4,
            "flush": 10,  # Higher flush bonus
            "full_house": 12,
            "quads": 20,
            "straight_flush": 30,
            "royal_flush": 50
        }
    )
    
    print(f"\nCustom config created:")
    print(f"- FL entry: {custom_config.fl_entry_requirement}")
    print(f"- FL stay: {custom_config.fl_stay_requirement}")
    print(f"- Middle flush bonus: {custom_config.royalty_middle['flush']} points")
    
    # In the future, services would accept config
    # manager = PineappleFantasyLandManager(custom_config)
    print("\nNote: Services will be updated to accept config in next iteration")


def compare_variants():
    """Compare different variant configurations."""
    print("\n=== Variant Comparison ===")
    
    variants = [
        PINEAPPLE_STANDARD,
        PINEAPPLE_POKERSTARS,
        STANDARD_OFC
    ]
    
    print("\n{:<20} {:<15} {:<15} {:<20}".format(
        "Variant", "Cards/Turn", "FL Entry", "FL Stay"
    ))
    print("-" * 70)
    
    for variant in variants:
        print("{:<20} {:<15} {:<15} {:<20}".format(
            variant.variant_name,
            f"{variant.cards_per_turn}→{variant.cards_to_place}",
            variant.fl_entry_requirement,
            variant.fl_stay_requirement[:20] + "..." if len(variant.fl_stay_requirement) > 20 else variant.fl_stay_requirement
        ))


def test_royalty_scoring():
    """Test royalty scoring configurations."""
    print("\n=== Royalty Scoring Comparison ===")
    
    config1 = PINEAPPLE_STANDARD
    config2 = GameVariantConfig(
        variant_name="high_royalty_variant",
        royalty_top={
            "QQ": 10,  # Higher than standard
            "KK": 12,
            "AA": 15,
            "222": 15,
            "333": 16,
            # ... etc
        }
    )
    
    print("\nTop row QQ royalty:")
    print(f"- Standard: {config1.royalty_top.get('QQ', 0)} points")
    print(f"- High variant: {config2.royalty_top.get('QQ', 0)} points")
    
    print("\nMiddle row flush royalty:")
    print(f"- Standard: {config1.royalty_middle.get('flush', 0)} points")
    print(f"- High variant: {config2.royalty_middle.get('flush', 0)} points")


def main():
    print("="*60)
    print("Game Variant Configuration Demo")
    print(f"Time: {datetime.now()}")
    print("="*60)
    
    # Show predefined configs
    print_config_details(PINEAPPLE_STANDARD)
    print_config_details(PINEAPPLE_POKERSTARS)
    print_config_details(STANDARD_OFC)
    
    # Test custom config
    test_config_with_fl_manager()
    
    # Compare variants
    compare_variants()
    
    # Test royalty scoring
    test_royalty_scoring()
    
    print("\n" + "="*60)
    print("Configuration system ready for multi-variant support! ✓")
    print("="*60)


if __name__ == "__main__":
    main()