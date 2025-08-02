"""
Unit tests for HandEvaluator domain service.
"""

import pytest

from src.domain.services.hand_evaluator import HandEvaluator
from src.domain.value_objects.card import Card
from src.domain.value_objects.hand_ranking import HandType


class TestHandEvaluator:
    """Test HandEvaluator service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = HandEvaluator()

    def test_evaluator_initialization(self):
        """Test hand evaluator initialization."""
        evaluator = HandEvaluator()
        assert evaluator is not None

    def test_evaluate_hand_invalid_size(self):
        """Test hand evaluation with invalid card count."""
        # Too few cards
        with pytest.raises(ValueError, match="Hand must have 3-5 cards"):
            self.evaluator.evaluate_hand(
                [Card.from_string("As"), Card.from_string("Kh")]
            )

        # Too many cards
        with pytest.raises(ValueError, match="Hand must have 3-5 cards"):
            self.evaluator.evaluate_hand(
                [
                    Card.from_string("As"),
                    Card.from_string("Kh"),
                    Card.from_string("Qc"),
                    Card.from_string("Jd"),
                    Card.from_string("Ts"),
                    Card.from_string("9h"),
                ]
            )


class TestHandEvaluationBasicHands:
    """Test basic hand evaluation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = HandEvaluator()

    def test_evaluate_high_card(self):
        """Test high card evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qc"),
            Card.from_string("Jd"),
            Card.from_string("9s"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.HIGH_CARD
        assert ranking.strength_value == 14  # Ace high
        assert ranking.kickers == [13, 12, 11, 9]  # K, Q, J, 9
        assert ranking.royalty_bonus == 0
        assert ranking.cards == cards

    def test_evaluate_pair(self):
        """Test pair evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
            Card.from_string("Qd"),
            Card.from_string("Js"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.PAIR
        assert ranking.strength_value == 14  # Pair of Aces
        assert ranking.kickers == [13, 12, 11]  # K, Q, J
        assert ranking.royalty_bonus == 0

    def test_evaluate_two_pair(self):
        """Test two pair evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
            Card.from_string("Kd"),
            Card.from_string("Qs"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.TWO_PAIR
        assert ranking.strength_value == 14  # Higher pair (Aces)
        assert ranking.kickers == [13, 12]  # Lower pair (Kings), kicker (Queen)
        assert ranking.royalty_bonus == 0

    def test_evaluate_three_of_a_kind(self):
        """Test three of a kind evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Ac"),
            Card.from_string("Kd"),
            Card.from_string("Qs"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.THREE_OF_A_KIND
        assert ranking.strength_value == 14  # Three Aces
        assert ranking.kickers == [13, 12]  # K, Q
        assert ranking.royalty_bonus == 0

    def test_evaluate_straight(self):
        """Test straight evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qc"),
            Card.from_string("Jd"),
            Card.from_string("Ts"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.STRAIGHT
        assert ranking.strength_value == 14  # Ace high straight
        assert ranking.kickers == []
        assert ranking.royalty_bonus == 2  # Straight royalty

    def test_evaluate_wheel_straight(self):
        """Test wheel straight (A-2-3-4-5) evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("2h"),
            Card.from_string("3c"),
            Card.from_string("4d"),
            Card.from_string("5s"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.STRAIGHT
        assert ranking.strength_value == 5  # 5-high straight (wheel)
        assert ranking.kickers == []
        assert ranking.royalty_bonus == 2  # Straight royalty

    def test_evaluate_flush(self):
        """Test flush evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("Qs"),
            Card.from_string("Js"),
            Card.from_string("9s"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.FLUSH
        assert ranking.strength_value == 14  # Ace high
        assert ranking.kickers == [13, 12, 11, 9]  # K, Q, J, 9
        assert ranking.royalty_bonus == 4  # Flush royalty

    def test_evaluate_full_house(self):
        """Test full house evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Ac"),
            Card.from_string("Ks"),
            Card.from_string("Kh"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.FULL_HOUSE
        assert ranking.strength_value == 14  # Three Aces
        assert ranking.kickers == [13]  # Pair of Kings
        assert ranking.royalty_bonus == 6  # Full house royalty

    def test_evaluate_four_of_a_kind(self):
        """Test four of a kind evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Ac"),
            Card.from_string("Ad"),
            Card.from_string("Ks"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.FOUR_OF_A_KIND
        assert ranking.strength_value == 14  # Four Aces
        assert ranking.kickers == [13]  # King kicker
        assert ranking.royalty_bonus == 10  # Four of a kind royalty

    def test_evaluate_straight_flush(self):
        """Test straight flush evaluation."""
        cards = [
            Card.from_string("9s"),
            Card.from_string("Ts"),
            Card.from_string("Js"),
            Card.from_string("Qs"),
            Card.from_string("Ks"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.STRAIGHT_FLUSH
        assert ranking.strength_value == 13  # King high straight flush
        assert ranking.kickers == []
        assert ranking.royalty_bonus == 15  # Straight flush royalty

    def test_evaluate_royal_flush(self):
        """Test royal flush evaluation."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("Qs"),
            Card.from_string("Js"),
            Card.from_string("Ts"),
        ]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.ROYAL_FLUSH
        assert ranking.strength_value == 14  # Ace high
        assert ranking.kickers == []
        assert ranking.royalty_bonus == 25  # Royal flush royalty


class TestHandEvaluationThreeCardHands:
    """Test three-card hand evaluation (top row)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = HandEvaluator()

    def test_evaluate_three_card_high_card(self):
        """Test three-card high card evaluation."""
        cards = [Card.from_string("As"), Card.from_string("Kh"), Card.from_string("Qc")]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.HIGH_CARD
        assert ranking.strength_value == 14  # Ace high
        assert ranking.royalty_bonus == 0  # No royalty for high card

    def test_evaluate_three_card_pair_no_royalty(self):
        """Test three-card pair without royalty."""
        cards = [Card.from_string("5s"), Card.from_string("5h"), Card.from_string("Kc")]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.PAIR
        assert ranking.strength_value == 5  # Pair of fives
        assert ranking.royalty_bonus == 0  # No royalty for pair below sixes

    def test_evaluate_three_card_pair_with_royalty(self):
        """Test three-card pair with royalty."""
        cards = [Card.from_string("6s"), Card.from_string("6h"), Card.from_string("Kc")]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.PAIR
        assert ranking.strength_value == 6  # Pair of sixes
        assert ranking.royalty_bonus == 1  # 6 - 5 = 1 royalty

        # Test higher pair
        ace_pair_cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
        ]
        ace_ranking = self.evaluator.evaluate_hand(ace_pair_cards)

        assert ace_ranking.hand_type == HandType.PAIR
        assert ace_ranking.strength_value == 14  # Pair of Aces
        assert ace_ranking.royalty_bonus == 9  # 14 - 5 = 9 royalty

    def test_evaluate_three_card_trips(self):
        """Test three-card trips evaluation."""
        cards = [Card.from_string("As"), Card.from_string("Ah"), Card.from_string("Ac")]

        ranking = self.evaluator.evaluate_hand(cards)

        assert ranking.hand_type == HandType.THREE_OF_A_KIND
        assert ranking.strength_value == 14  # Three Aces
        assert ranking.royalty_bonus == 10  # Trips royalty


class TestHandComparison:
    """Test hand comparison functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = HandEvaluator()

    def test_compare_hands_different_types(self):
        """Test comparing hands of different types."""
        pair_cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
        ]
        high_card_cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qc"),
        ]

        pair_ranking = self.evaluator.evaluate_hand(pair_cards)
        high_card_ranking = self.evaluator.evaluate_hand(high_card_cards)

        assert (
            self.evaluator.compare_hands(pair_ranking, high_card_ranking) == 1
        )  # Pair wins
        assert (
            self.evaluator.compare_hands(high_card_ranking, pair_ranking) == -1
        )  # High card loses

    def test_compare_hands_same_type(self):
        """Test comparing hands of same type."""
        ace_pair_cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
        ]
        king_pair_cards = [
            Card.from_string("Ks"),
            Card.from_string("Kh"),
            Card.from_string("Ac"),
        ]

        ace_pair = self.evaluator.evaluate_hand(ace_pair_cards)
        king_pair = self.evaluator.evaluate_hand(king_pair_cards)

        assert self.evaluator.compare_hands(ace_pair, king_pair) == 1  # Ace pair wins
        assert (
            self.evaluator.compare_hands(king_pair, ace_pair) == -1
        )  # King pair loses

    def test_compare_hands_tie(self):
        """Test comparing identical hands."""
        cards1 = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
        ]
        cards2 = [
            Card.from_string("Ad"),
            Card.from_string("Ac"),
            Card.from_string("Kd"),
        ]

        ranking1 = self.evaluator.evaluate_hand(cards1)
        ranking2 = self.evaluator.evaluate_hand(cards2)

        assert self.evaluator.compare_hands(ranking1, ranking2) == 0  # Tie


class TestOFCValidation:
    """Test OFC-specific validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = HandEvaluator()

    def test_validate_ofc_progression_valid(self):
        """Test valid OFC hand progression."""
        # Bottom > Middle > Top (valid progression)
        top_cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qc"),
        ]  # A high
        middle_cards = [
            Card.from_string("2s"),
            Card.from_string("2h"),
            Card.from_string("3c"),
            Card.from_string("3d"),
            Card.from_string("4s"),
        ]  # Two pair
        bottom_cards = [
            Card.from_string("5s"),
            Card.from_string("5h"),
            Card.from_string("5c"),
            Card.from_string("6d"),
            Card.from_string("6s"),
        ]  # Full house

        is_valid = self.evaluator.validate_ofc_progression(
            top_cards, middle_cards, bottom_cards
        )
        assert is_valid

    def test_validate_ofc_progression_invalid_card_count(self):
        """Test OFC validation with wrong card counts."""
        top_cards = [Card.from_string("As"), Card.from_string("Kh")]  # Only 2 cards
        middle_cards = [
            Card.from_string("2s"),
            Card.from_string("2h"),
            Card.from_string("3c"),
            Card.from_string("3d"),
            Card.from_string("4s"),
        ]
        bottom_cards = [
            Card.from_string("5s"),
            Card.from_string("5h"),
            Card.from_string("5c"),
            Card.from_string("6d"),
            Card.from_string("6s"),
        ]

        is_valid = self.evaluator.validate_ofc_progression(
            top_cards, middle_cards, bottom_cards
        )
        assert not is_valid

    def test_validate_ofc_progression_fouled(self):
        """Test fouled OFC hand progression."""
        # Top > Middle (fouled)
        top_cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
        ]  # Pair of Aces
        middle_cards = [
            Card.from_string("Ks"),
            Card.from_string("Qh"),
            Card.from_string("Jc"),
            Card.from_string("7d"),
            Card.from_string("3s"),
        ]  # King high (not a straight)
        bottom_cards = [
            Card.from_string("5s"),
            Card.from_string("5h"),
            Card.from_string("5c"),
            Card.from_string("6d"),
            Card.from_string("6s"),
        ]  # Full house

        is_valid = self.evaluator.validate_ofc_progression(
            top_cards, middle_cards, bottom_cards
        )
        assert not is_valid  # Should be fouled


class TestRoyaltyCalculation:
    """Test royalty bonus calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = HandEvaluator()

    def test_top_row_royalty_calculation(self):
        """Test top row royalty calculation."""
        # Pair of sixes (minimum for royalty)
        sixes_cards = [
            Card.from_string("6s"),
            Card.from_string("6h"),
            Card.from_string("Kc"),
        ]
        sixes_ranking = self.evaluator.evaluate_hand(sixes_cards)
        assert sixes_ranking.royalty_bonus == 1

        # Pair of Aces (maximum pair royalty)
        aces_cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
        ]
        aces_ranking = self.evaluator.evaluate_hand(aces_cards)
        assert aces_ranking.royalty_bonus == 9  # 14 - 5 = 9

        # Three of a kind
        trips_cards = [
            Card.from_string("2s"),
            Card.from_string("2h"),
            Card.from_string("2c"),
        ]
        trips_ranking = self.evaluator.evaluate_hand(trips_cards)
        assert trips_ranking.royalty_bonus == 10

    def test_five_card_royalty_calculation(self):
        """Test five-card hand royalty calculation."""
        # Straight
        straight_cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qc"),
            Card.from_string("Jd"),
            Card.from_string("Ts"),
        ]
        straight_ranking = self.evaluator.evaluate_hand(straight_cards)
        assert straight_ranking.royalty_bonus == 2

        # Flush
        flush_cards = [
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("Qs"),
            Card.from_string("Js"),
            Card.from_string("9s"),
        ]
        flush_ranking = self.evaluator.evaluate_hand(flush_cards)
        assert flush_ranking.royalty_bonus == 4

        # Full house
        full_house_cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Ac"),
            Card.from_string("Ks"),
            Card.from_string("Kh"),
        ]
        full_house_ranking = self.evaluator.evaluate_hand(full_house_cards)
        assert full_house_ranking.royalty_bonus == 6

        # Four of a kind
        quads_cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Ac"),
            Card.from_string("Ad"),
            Card.from_string("Ks"),
        ]
        quads_ranking = self.evaluator.evaluate_hand(quads_cards)
        assert quads_ranking.royalty_bonus == 10

        # Straight flush
        straight_flush_cards = [
            Card.from_string("9s"),
            Card.from_string("Ts"),
            Card.from_string("Js"),
            Card.from_string("Qs"),
            Card.from_string("Ks"),
        ]
        straight_flush_ranking = self.evaluator.evaluate_hand(straight_flush_cards)
        assert straight_flush_ranking.royalty_bonus == 15

        # Royal flush
        royal_flush_cards = [
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("Qs"),
            Card.from_string("Js"),
            Card.from_string("Ts"),
        ]
        royal_flush_ranking = self.evaluator.evaluate_hand(royal_flush_cards)
        assert royal_flush_ranking.royalty_bonus == 25


class TestFouledHandDetection:
    """Test fouled hand detection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = HandEvaluator()

    def test_is_fouled_hand_method(self):
        """Test the is_fouled_hand method."""
        # Valid progression
        top_cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qc"),
        ]  # A high
        middle_cards = [
            Card.from_string("2s"),
            Card.from_string("2h"),
            Card.from_string("3c"),
            Card.from_string("3d"),
            Card.from_string("4s"),
        ]  # Two pair
        bottom_cards = [
            Card.from_string("5s"),
            Card.from_string("5h"),
            Card.from_string("5c"),
            Card.from_string("6d"),
            Card.from_string("6s"),
        ]  # Full house

        assert not self.evaluator.is_fouled_hand(top_cards, middle_cards, bottom_cards)

        # Fouled hand
        fouled_top = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
        ]  # Pair
        fouled_middle = [
            Card.from_string("Ks"),
            Card.from_string("Qh"),
            Card.from_string("Jc"),
            Card.from_string("7d"),
            Card.from_string("3s"),
        ]  # K high

        assert self.evaluator.is_fouled_hand(fouled_top, fouled_middle, bottom_cards)


class TestPerformanceOptimization:
    """Test performance optimization features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = HandEvaluator()

    def test_evaluation_caching(self):
        """Test that hand evaluations are cached."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qc"),
            Card.from_string("Jd"),
            Card.from_string("Ts"),
        ]

        # First evaluation
        result1 = self.evaluator.evaluate_hand(cards)

        # Second evaluation with same cards (should use cache)
        result2 = self.evaluator.evaluate_hand(cards)

        # Results should be equal
        assert result1.hand_type == result2.hand_type
        assert result1.strength_value == result2.strength_value
        assert result1.royalty_bonus == result2.royalty_bonus

        # Different card order should still use cache
        shuffled_cards = [cards[2], cards[0], cards[4], cards[1], cards[3]]
        result3 = self.evaluator.evaluate_hand(shuffled_cards)

        assert result1.hand_type == result3.hand_type
        assert result1.strength_value == result3.strength_value

    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        cards = [Card.from_string("As"), Card.from_string("Kh"), Card.from_string("Qc")]

        # Evaluate and cache
        self.evaluator.evaluate_hand(cards)
        assert len(self.evaluator._evaluation_cache) > 0

        # Clear cache
        self.evaluator.clear_cache()
        assert len(self.evaluator._evaluation_cache) == 0


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = HandEvaluator()

    def test_straight_edge_cases(self):
        """Test straight edge cases."""
        # Regular straight (not flush)
        regular_straight = [
            Card.from_string("5s"),
            Card.from_string("6h"),
            Card.from_string("7c"),
            Card.from_string("8d"),
            Card.from_string("9s"),
        ]
        ranking = self.evaluator.evaluate_hand(regular_straight)
        assert ranking.hand_type == HandType.STRAIGHT
        assert ranking.strength_value == 9  # 9-high straight

        # Wheel straight
        wheel_straight = [
            Card.from_string("As"),
            Card.from_string("2h"),
            Card.from_string("3c"),
            Card.from_string("4d"),
            Card.from_string("5s"),
        ]
        wheel_ranking = self.evaluator.evaluate_hand(wheel_straight)
        assert wheel_ranking.hand_type == HandType.STRAIGHT
        assert wheel_ranking.strength_value == 5  # 5-high straight (wheel)

    def test_flush_vs_straight(self):
        """Test that flush beats straight."""
        flush_cards = [
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("Qs"),
            Card.from_string("Js"),
            Card.from_string("9s"),
        ]
        straight_cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qc"),
            Card.from_string("Jd"),
            Card.from_string("Ts"),
        ]

        flush_ranking = self.evaluator.evaluate_hand(flush_cards)
        straight_ranking = self.evaluator.evaluate_hand(straight_cards)

        assert (
            self.evaluator.compare_hands(flush_ranking, straight_ranking) == 1
        )  # Flush wins

    def test_kicker_comparison(self):
        """Test kicker comparison for same hand types."""
        # Two pairs with different kickers
        pair1_cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
            Card.from_string("Qd"),
            Card.from_string("Js"),
        ]
        pair2_cards = [
            Card.from_string("Ad"),
            Card.from_string("Ac"),
            Card.from_string("Kd"),
            Card.from_string("Qh"),
            Card.from_string("Ts"),
        ]

        pair1_ranking = self.evaluator.evaluate_hand(pair1_cards)
        pair2_ranking = self.evaluator.evaluate_hand(pair2_cards)

        # Same pair (Aces), same first two kickers (K, Q), but J > T
        assert self.evaluator.compare_hands(pair1_ranking, pair2_ranking) == 1

    def test_three_card_hand_edge_cases(self):
        """Test edge cases specific to 3-card hands."""
        # Three different cards (high card)
        high_card = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("2c"),
        ]
        ranking = self.evaluator.evaluate_hand(high_card)
        assert ranking.hand_type == HandType.HIGH_CARD
        assert ranking.strength_value == 14

        # Three of a kind with minimum rank
        trips_twos = [
            Card.from_string("2s"),
            Card.from_string("2h"),
            Card.from_string("2c"),
        ]
        trips_ranking = self.evaluator.evaluate_hand(trips_twos)
        assert trips_ranking.hand_type == HandType.THREE_OF_A_KIND
        assert trips_ranking.royalty_bonus == 10  # All trips in top row get 10

    def test_duplicate_ranks_different_suits(self):
        """Test hands with duplicate ranks but different suits."""
        # Four cards of same rank plus one different (only possible with 5 cards)
        four_aces = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Ac"),
            Card.from_string("Ad"),
            Card.from_string("Ks"),
        ]
        ranking = self.evaluator.evaluate_hand(four_aces)
        assert ranking.hand_type == HandType.FOUR_OF_A_KIND
        assert ranking.strength_value == 14

    def test_mixed_straight_and_flush_cards(self):
        """Test hands that are almost straights or flushes."""
        # Four cards to a straight
        almost_straight = [
            Card.from_string("5s"),
            Card.from_string("6h"),
            Card.from_string("7c"),
            Card.from_string("8d"),
            Card.from_string("Ks"),
        ]
        ranking = self.evaluator.evaluate_hand(almost_straight)
        assert ranking.hand_type == HandType.HIGH_CARD

        # Four cards to a flush
        almost_flush = [
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("Qs"),
            Card.from_string("Js"),
            Card.from_string("9h"),
        ]
        ranking = self.evaluator.evaluate_hand(almost_flush)
        assert ranking.hand_type == HandType.HIGH_CARD
