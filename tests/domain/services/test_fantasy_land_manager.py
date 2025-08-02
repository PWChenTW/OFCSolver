"""
Tests for Fantasy Land Manager Domain Service
"""

import pytest

from src.domain.services import FantasyLandManager, HandEvaluator
from src.domain.value_objects import Card, HandRanking
from src.domain.value_objects.hand_ranking import HandType


class TestFantasyLandManager:
    """Test suite for Fantasy Land Manager service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = FantasyLandManager()
        self.evaluator = HandEvaluator()

    def test_initialization(self):
        """Test service initialization."""
        manager = FantasyLandManager()
        assert isinstance(manager, FantasyLandManager)

    def test_qualifies_top_row_queens(self):
        """Test qualification with QQ in top row."""
        # QQ in top row qualifies
        top_cards = Card.parse_cards("Qs Qh As")
        top_hand = self.evaluator.evaluate_hand(top_cards)
        
        assert self.manager.qualifies_for_fantasy_land(top_hand=top_hand)

    def test_qualifies_top_row_better_pair(self):
        """Test qualification with better pairs in top row."""
        # KK in top row qualifies
        top_cards = Card.parse_cards("Ks Kh As")
        top_hand = self.evaluator.evaluate_hand(top_cards)
        
        assert self.manager.qualifies_for_fantasy_land(top_hand=top_hand)
        
        # AA in top row qualifies
        top_cards = Card.parse_cards("As Ah Ks")
        top_hand = self.evaluator.evaluate_hand(top_cards)
        
        assert self.manager.qualifies_for_fantasy_land(top_hand=top_hand)

    def test_not_qualifies_top_row_weak_pair(self):
        """Test non-qualification with weak pairs in top row."""
        # JJ in top row doesn't qualify
        top_cards = Card.parse_cards("Js Jh As")
        top_hand = self.evaluator.evaluate_hand(top_cards)
        
        assert not self.manager.qualifies_for_fantasy_land(top_hand=top_hand)
        
        # 22 in top row doesn't qualify
        top_cards = Card.parse_cards("2s 2h As")
        top_hand = self.evaluator.evaluate_hand(top_cards)
        
        assert not self.manager.qualifies_for_fantasy_land(top_hand=top_hand)

    def test_qualifies_top_row_trips(self):
        """Test qualification with three of a kind in top row."""
        # Any trips in top row qualifies
        top_cards = Card.parse_cards("2s 2h 2d")
        top_hand = self.evaluator.evaluate_hand(top_cards)
        
        assert self.manager.qualifies_for_fantasy_land(top_hand=top_hand)

    def test_qualifies_middle_row_trips(self):
        """Test qualification with three of a kind in middle row."""
        middle_cards = Card.parse_cards("7s 7h 7d Ks Qs")
        middle_hand = self.evaluator.evaluate_hand(middle_cards)
        
        assert self.manager.qualifies_for_fantasy_land(middle_hand=middle_hand)

    def test_qualifies_middle_row_better_hands(self):
        """Test qualification with better hands in middle row."""
        # Full house in middle qualifies
        middle_cards = Card.parse_cards("Ks Kh Kd 2s 2h")
        middle_hand = self.evaluator.evaluate_hand(middle_cards)
        
        assert self.manager.qualifies_for_fantasy_land(middle_hand=middle_hand)
        
        # Four of a kind in middle qualifies
        middle_cards = Card.parse_cards("9s 9h 9d 9c As")
        middle_hand = self.evaluator.evaluate_hand(middle_cards)
        
        assert self.manager.qualifies_for_fantasy_land(middle_hand=middle_hand)

    def test_not_qualifies_middle_row_weak_hands(self):
        """Test non-qualification with weak hands in middle row."""
        # Two pair doesn't qualify
        middle_cards = Card.parse_cards("Ks Kh Qs Qh As")
        middle_hand = self.evaluator.evaluate_hand(middle_cards)
        
        assert not self.manager.qualifies_for_fantasy_land(middle_hand=middle_hand)
        
        # Pair doesn't qualify
        middle_cards = Card.parse_cards("As Ah Ks Qs Js")
        middle_hand = self.evaluator.evaluate_hand(middle_cards)
        
        assert not self.manager.qualifies_for_fantasy_land(middle_hand=middle_hand)

    def test_qualifies_bottom_row_straight(self):
        """Test qualification with straight in bottom row."""
        bottom_cards = Card.parse_cards("5s 4h 3d 2c As")
        bottom_hand = self.evaluator.evaluate_hand(bottom_cards)
        
        assert self.manager.qualifies_for_fantasy_land(bottom_hand=bottom_hand)

    def test_qualifies_bottom_row_better_hands(self):
        """Test qualification with better hands in bottom row."""
        # Flush qualifies
        bottom_cards = Card.parse_cards("Ks Qs 8s 5s 2s")
        bottom_hand = self.evaluator.evaluate_hand(bottom_cards)
        
        assert self.manager.qualifies_for_fantasy_land(bottom_hand=bottom_hand)
        
        # Full house qualifies
        bottom_cards = Card.parse_cards("As Ah Ad Ks Kh")
        bottom_hand = self.evaluator.evaluate_hand(bottom_cards)
        
        assert self.manager.qualifies_for_fantasy_land(bottom_hand=bottom_hand)

    def test_not_qualifies_bottom_row_weak_hands(self):
        """Test non-qualification with weak hands in bottom row."""
        # Three of a kind doesn't qualify
        bottom_cards = Card.parse_cards("7s 7h 7d Ks Qs")
        bottom_hand = self.evaluator.evaluate_hand(bottom_cards)
        
        assert not self.manager.qualifies_for_fantasy_land(bottom_hand=bottom_hand)

    def test_qualifies_multiple_rows(self):
        """Test qualification when multiple rows qualify."""
        # QQ in top
        top_cards = Card.parse_cards("Qs Qh As")
        top_hand = self.evaluator.evaluate_hand(top_cards)
        
        # Trips in middle
        middle_cards = Card.parse_cards("7s 7h 7d Ks Qs")
        middle_hand = self.evaluator.evaluate_hand(middle_cards)
        
        # Should qualify with either
        assert self.manager.qualifies_for_fantasy_land(
            top_hand=top_hand,
            middle_hand=middle_hand
        )

    def test_can_stay_in_fantasy_land_top_trips(self):
        """Test staying in fantasy land with trips in top."""
        top_cards = Card.parse_cards("As Ah Ad")
        top_hand = self.evaluator.evaluate_hand(top_cards)
        
        assert self.manager.can_stay_in_fantasy_land(top_hand=top_hand)

    def test_can_stay_in_fantasy_land_middle_full_house(self):
        """Test staying in fantasy land with full house in middle."""
        middle_cards = Card.parse_cards("Ks Kh Kd 2s 2h")
        middle_hand = self.evaluator.evaluate_hand(middle_cards)
        
        assert self.manager.can_stay_in_fantasy_land(middle_hand=middle_hand)

    def test_can_stay_in_fantasy_land_bottom_quads(self):
        """Test staying in fantasy land with four of a kind in bottom."""
        bottom_cards = Card.parse_cards("9s 9h 9d 9c As")
        bottom_hand = self.evaluator.evaluate_hand(bottom_cards)
        
        assert self.manager.can_stay_in_fantasy_land(bottom_hand=bottom_hand)

    def test_cannot_stay_weak_hands(self):
        """Test cannot stay with hands that only qualify for entry."""
        # QQ in top (qualifies for entry but not stay)
        top_cards = Card.parse_cards("Qs Qh As")
        top_hand = self.evaluator.evaluate_hand(top_cards)
        
        # Trips in middle (qualifies for entry but not stay)
        middle_cards = Card.parse_cards("7s 7h 7d Ks Qs")
        middle_hand = self.evaluator.evaluate_hand(middle_cards)
        
        # Straight in bottom (qualifies for entry but not stay)
        bottom_cards = Card.parse_cards("5s 4h 3d 2c As")
        bottom_hand = self.evaluator.evaluate_hand(bottom_cards)
        
        assert not self.manager.can_stay_in_fantasy_land(
            top_hand=top_hand,
            middle_hand=middle_hand,
            bottom_hand=bottom_hand
        )

    def test_get_fantasy_land_card_count(self):
        """Test getting card count for different variants."""
        assert self.manager.get_fantasy_land_card_count("standard") == 13
        assert self.manager.get_fantasy_land_card_count("pineapple") == 14
        assert self.manager.get_fantasy_land_card_count("2-7-pineapple") == 14
        assert self.manager.get_fantasy_land_card_count("unknown") == 13  # Default

    def test_validate_fantasy_land_setting_valid(self):
        """Test validating valid fantasy land card setting."""
        # Standard - 13 cards
        cards = Card.create_deck()[:13]
        assert self.manager.validate_fantasy_land_setting(cards, "standard")
        
        # Pineapple - 14 cards
        cards = Card.create_deck()[:14]
        assert self.manager.validate_fantasy_land_setting(cards, "pineapple")

    def test_validate_fantasy_land_setting_wrong_count(self):
        """Test validating with wrong card count."""
        # Too few cards
        cards = Card.create_deck()[:12]
        assert not self.manager.validate_fantasy_land_setting(cards, "standard")
        
        # Too many cards
        cards = Card.create_deck()[:15]
        assert not self.manager.validate_fantasy_land_setting(cards, "pineapple")

    def test_validate_fantasy_land_setting_duplicates(self):
        """Test validating with duplicate cards."""
        # Create cards with duplicates
        cards = Card.parse_cards("As Ks Qs Js Ts 9s 8s 7s 6s 5s 4s 3s As")  # As appears twice
        assert not self.manager.validate_fantasy_land_setting(cards, "standard")

    def test_get_qualification_requirements(self):
        """Test getting qualification requirements."""
        requirements = self.manager.get_qualification_requirements()
        
        assert isinstance(requirements, dict)
        assert "initial_qualification" in requirements
        assert "stay_requirements" in requirements
        assert "card_count" in requirements
        
        # Check initial requirements
        assert requirements["initial_qualification"]["top"] == "QQ or better (pair of queens or higher)"
        assert requirements["initial_qualification"]["middle"] == "Three of a kind or better"
        assert requirements["initial_qualification"]["bottom"] == "Straight or better"
        
        # Check stay requirements
        assert requirements["stay_requirements"]["top"] == "Three of a kind"
        assert requirements["stay_requirements"]["middle"] == "Full house or better"
        assert requirements["stay_requirements"]["bottom"] == "Four of a kind or better"

    def test_calculate_fantasy_land_probability(self):
        """Test fantasy land probability calculation."""
        cards_seen = Card.parse_cards("As Ks Qs Js Ts")
        
        # Top row probability
        top_prob = self.manager.calculate_fantasy_land_probability(cards_seen, "top")
        assert 0 <= top_prob <= 1
        assert 0.1 <= top_prob <= 0.25  # Reasonable range for QQ+
        
        # Middle row probability
        middle_prob = self.manager.calculate_fantasy_land_probability(cards_seen, "middle")
        assert 0 <= middle_prob <= 1
        assert 0.05 <= middle_prob <= 0.20  # Reasonable range for trips+
        
        # Bottom row probability
        bottom_prob = self.manager.calculate_fantasy_land_probability(cards_seen, "bottom")
        assert 0 <= bottom_prob <= 1
        assert 0.20 <= bottom_prob <= 0.40  # Reasonable range for straight+
        
        # Invalid position
        invalid_prob = self.manager.calculate_fantasy_land_probability(cards_seen, "invalid")
        assert invalid_prob == 0.0

    def test_probability_decreases_with_more_cards_seen(self):
        """Test that probability decreases as more cards are seen."""
        few_cards = Card.parse_cards("As Ks")
        many_cards = Card.parse_cards("As Ks Qs Js Ts 9s 8s 7s 6s 5s")
        
        # Probabilities should be lower with more cards seen
        top_few = self.manager.calculate_fantasy_land_probability(few_cards, "top")
        top_many = self.manager.calculate_fantasy_land_probability(many_cards, "top")
        assert top_few > top_many