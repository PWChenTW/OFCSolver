"""
Unit tests for HandRanking value object.
"""

import pytest

from src.domain.value_objects.card import Card, Rank, Suit
from src.domain.value_objects.hand_ranking import HandRanking, HandType


class TestHandType:
    """Test HandType functionality."""

    def test_hand_type_creation(self):
        """Test hand type creation and properties."""
        hand_type = HandType.FLUSH
        assert hand_type.value == 5
        assert hand_type.display_name == "Flush"
        assert str(hand_type) == "Flush"

    def test_hand_type_comparison(self):
        """Test hand type comparison operations."""
        assert HandType.HIGH_CARD < HandType.PAIR
        assert HandType.PAIR < HandType.ROYAL_FLUSH
        assert HandType.FULL_HOUSE > HandType.FLUSH
        assert HandType.STRAIGHT <= HandType.FLUSH
        assert HandType.FLUSH >= HandType.STRAIGHT
        assert HandType.PAIR == HandType.PAIR

    def test_hand_type_ordering(self):
        """Test complete hand type ordering."""
        types_in_order = [
            HandType.HIGH_CARD,
            HandType.PAIR,
            HandType.TWO_PAIR,
            HandType.THREE_OF_A_KIND,
            HandType.STRAIGHT,
            HandType.FLUSH,
            HandType.FULL_HOUSE,
            HandType.FOUR_OF_A_KIND,
            HandType.STRAIGHT_FLUSH,
            HandType.ROYAL_FLUSH,
        ]

        for i in range(len(types_in_order) - 1):
            assert types_in_order[i] < types_in_order[i + 1]


class TestHandRankingCreation:
    """Test HandRanking creation and validation."""

    def test_hand_ranking_creation(self):
        """Test basic hand ranking creation."""
        cards = [Card.from_string("As"), Card.from_string("Ks"), Card.from_string("Qs")]
        hand_ranking = HandRanking(
            hand_type=HandType.HIGH_CARD,
            strength_value=14,  # Ace high
            kickers=[13, 12],  # King, Queen
            royalty_bonus=0,
            cards=cards,
        )

        assert hand_ranking.hand_type == HandType.HIGH_CARD
        assert hand_ranking.strength_value == 14
        assert hand_ranking.kickers == [13, 12]
        assert hand_ranking.royalty_bonus == 0
        assert hand_ranking.cards == cards

    def test_hand_ranking_validation(self):
        """Test hand ranking validation."""
        cards = [Card.from_string("As"), Card.from_string("Ks"), Card.from_string("Qs")]

        # Invalid hand type
        with pytest.raises(TypeError, match="hand_type must be a HandType instance"):
            HandRanking(
                hand_type="invalid",
                strength_value=14,
                kickers=[],
                royalty_bonus=0,
                cards=cards,
            )

        # Negative strength value
        with pytest.raises(ValueError, match="strength_value must be non-negative"):
            HandRanking(
                hand_type=HandType.HIGH_CARD,
                strength_value=-1,
                kickers=[],
                royalty_bonus=0,
                cards=cards,
            )

        # Negative royalty bonus
        with pytest.raises(ValueError, match="royalty_bonus must be non-negative"):
            HandRanking(
                hand_type=HandType.HIGH_CARD,
                strength_value=14,
                kickers=[],
                royalty_bonus=-1,
                cards=cards,
            )

        # Empty cards
        with pytest.raises(ValueError, match="cards list cannot be empty"):
            HandRanking(
                hand_type=HandType.HIGH_CARD,
                strength_value=14,
                kickers=[],
                royalty_bonus=0,
                cards=[],
            )

        # Too few cards
        with pytest.raises(ValueError, match="Hand must have 3-5 cards"):
            HandRanking(
                hand_type=HandType.HIGH_CARD,
                strength_value=14,
                kickers=[],
                royalty_bonus=0,
                cards=[Card.from_string("As"), Card.from_string("Ks")],  # Only 2 cards
            )

        # Too many cards
        with pytest.raises(ValueError, match="Hand must have 3-5 cards"):
            HandRanking(
                hand_type=HandType.HIGH_CARD,
                strength_value=14,
                kickers=[],
                royalty_bonus=0,
                cards=[Card.from_string(f"{rank}s") for rank in "AKQJT9"],  # 6 cards
            )


class TestHandRankingProperties:
    """Test HandRanking property methods."""

    def test_is_made_hand(self):
        """Test made hand checking."""
        # High card is not a made hand
        high_card = HandRanking(
            hand_type=HandType.HIGH_CARD,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
        )
        assert not high_card.is_made_hand

        # Pair is a made hand
        pair = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )
        assert pair.is_made_hand

    def test_is_premium_hand(self):
        """Test premium hand checking."""
        # Pair is not premium
        pair = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )
        assert not pair.is_premium_hand

        # Three of a kind is premium
        trips = HandRanking(
            hand_type=HandType.THREE_OF_A_KIND,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Ac"),
            ],
        )
        assert trips.is_premium_hand

    def test_is_monster_hand(self):
        """Test monster hand checking."""
        # Full house is not monster
        full_house = HandRanking(
            hand_type=HandType.FULL_HOUSE,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Ac"),
                Card.from_string("Ks"),
                Card.from_string("Kh"),
            ],
        )
        assert not full_house.is_monster_hand

        # Straight is monster
        straight = HandRanking(
            hand_type=HandType.STRAIGHT,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
                Card.from_string("Jd"),
                Card.from_string("Ts"),
            ],
        )
        assert straight.is_monster_hand

    def test_has_royalty(self):
        """Test royalty bonus checking."""
        # No royalty
        no_royalty = HandRanking(
            hand_type=HandType.HIGH_CARD,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
        )
        assert not no_royalty.has_royalty

        # Has royalty
        with_royalty = HandRanking(
            hand_type=HandType.FLUSH,
            strength_value=14,
            kickers=[],
            royalty_bonus=4,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ks"),
                Card.from_string("Qs"),
                Card.from_string("Js"),
                Card.from_string("9s"),
            ],
        )
        assert with_royalty.has_royalty

    def test_total_value(self):
        """Test total value calculation."""
        hand_ranking = HandRanking(
            hand_type=HandType.FLUSH,
            strength_value=14,
            kickers=[],
            royalty_bonus=4,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ks"),
                Card.from_string("Qs"),
                Card.from_string("Js"),
                Card.from_string("9s"),
            ],
        )

        assert hand_ranking.total_value == 18  # 14 + 4


class TestHandRankingComparison:
    """Test HandRanking comparison methods."""

    def test_compare_to_different_types(self):
        """Test comparison between different hand types."""
        pair = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )

        high_card = HandRanking(
            hand_type=HandType.HIGH_CARD,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
        )

        assert pair.compare_to(high_card) == 1  # Pair wins
        assert high_card.compare_to(pair) == -1  # High card loses

    def test_compare_to_same_type_different_strength(self):
        """Test comparison within same hand type."""
        ace_pair = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,  # Pair of Aces
            kickers=[13],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )

        king_pair = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=13,  # Pair of Kings
            kickers=[14],
            royalty_bonus=0,
            cards=[
                Card.from_string("Ks"),
                Card.from_string("Kh"),
                Card.from_string("Ac"),
            ],
        )

        assert ace_pair.compare_to(king_pair) == 1  # Ace pair wins
        assert king_pair.compare_to(ace_pair) == -1  # King pair loses

    def test_compare_to_same_strength_different_kickers(self):
        """Test comparison with same hand type and strength but different kickers."""
        pair_king_kicker = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,  # Pair of Aces
            kickers=[13, 12],  # King, Queen kickers
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
                Card.from_string("Qd"),
                Card.from_string("Js"),
            ],
        )

        pair_queen_kicker = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,  # Pair of Aces
            kickers=[12, 11],  # Queen, Jack kickers
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Qc"),
                Card.from_string("Jd"),
                Card.from_string("9s"),
            ],
        )

        assert pair_king_kicker.compare_to(pair_queen_kicker) == 1  # King kicker wins
        assert (
            pair_queen_kicker.compare_to(pair_king_kicker) == -1
        )  # Queen kicker loses

    def test_compare_to_tie(self):
        """Test comparison resulting in tie."""
        hand1 = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[13, 12],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )

        hand2 = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[13, 12],
            royalty_bonus=0,
            cards=[
                Card.from_string("Ad"),
                Card.from_string("Ac"),
                Card.from_string("Kd"),
            ],
        )

        assert hand1.compare_to(hand2) == 0  # Tie

    def test_convenience_comparison_methods(self):
        """Test convenience comparison methods."""
        stronger = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )

        weaker = HandRanking(
            hand_type=HandType.HIGH_CARD,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
        )

        # Test beats method
        assert stronger.beats(weaker)
        assert not weaker.beats(stronger)

        # Test loses_to method
        assert weaker.loses_to(stronger)
        assert not stronger.loses_to(weaker)

        # Test ties_with method
        assert not stronger.ties_with(weaker)

        # Test with identical hands
        identical = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("Ad"),
                Card.from_string("Ac"),
                Card.from_string("Kd"),
            ],
        )

        assert stronger.ties_with(identical)

    def test_comparison_operators(self):
        """Test comparison operators."""
        stronger = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )

        weaker = HandRanking(
            hand_type=HandType.HIGH_CARD,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
        )

        assert stronger > weaker
        assert stronger >= weaker
        assert weaker < stronger
        assert weaker <= stronger
        assert not (stronger == weaker)


class TestHandRankingDescription:
    """Test HandRanking description methods."""

    def test_get_hand_description_high_card(self):
        """Test high card description."""
        hand = HandRanking(
            hand_type=HandType.HIGH_CARD,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
        )

        description = hand.get_hand_description()
        assert "A High" in description

    def test_get_hand_description_pair(self):
        """Test pair description."""
        hand = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )

        description = hand.get_hand_description()
        assert "Pair of As" in description

    def test_get_hand_description_two_pair(self):
        """Test two pair description."""
        hand = HandRanking(
            hand_type=HandType.TWO_PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
                Card.from_string("Kd"),
                Card.from_string("Qs"),
            ],
        )

        description = hand.get_hand_description()
        assert "As and Ks" in description or "Ks and As" in description

    def test_get_hand_description_trips(self):
        """Test three of a kind description."""
        hand = HandRanking(
            hand_type=HandType.THREE_OF_A_KIND,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Ac"),
            ],
        )

        description = hand.get_hand_description()
        assert "Three As" in description

    def test_get_hand_description_straight(self):
        """Test straight description."""
        hand = HandRanking(
            hand_type=HandType.STRAIGHT,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
                Card.from_string("Jd"),
                Card.from_string("Ts"),
            ],
        )

        description = hand.get_hand_description()
        assert "Straight (A High)" in description

        # Test wheel straight
        wheel = HandRanking(
            hand_type=HandType.STRAIGHT,
            strength_value=5,  # 5-high straight
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("5s"),
                Card.from_string("4h"),
                Card.from_string("3c"),
                Card.from_string("2d"),
                Card.from_string("As"),
            ],
        )

        wheel_desc = wheel.get_hand_description()
        assert "Straight (5 High)" in wheel_desc

    def test_get_hand_description_flush(self):
        """Test flush description."""
        hand = HandRanking(
            hand_type=HandType.FLUSH,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ks"),
                Card.from_string("Qs"),
                Card.from_string("Js"),
                Card.from_string("9s"),
            ],
        )

        description = hand.get_hand_description()
        assert "♠ Flush (A High)" in description

    def test_get_hand_description_full_house(self):
        """Test full house description."""
        hand = HandRanking(
            hand_type=HandType.FULL_HOUSE,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Ac"),
                Card.from_string("Ks"),
                Card.from_string("Kh"),
            ],
        )

        description = hand.get_hand_description()
        assert "As full of Ks" in description

    def test_get_hand_description_quads(self):
        """Test four of a kind description."""
        hand = HandRanking(
            hand_type=HandType.FOUR_OF_A_KIND,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Ac"),
                Card.from_string("Ad"),
                Card.from_string("Ks"),
            ],
        )

        description = hand.get_hand_description()
        assert "Four As" in description

    def test_get_hand_description_straight_flush(self):
        """Test straight flush description."""
        hand = HandRanking(
            hand_type=HandType.STRAIGHT_FLUSH,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ks"),
                Card.from_string("Qs"),
                Card.from_string("Js"),
                Card.from_string("Ts"),
            ],
        )

        description = hand.get_hand_description()
        assert "♠ Straight Flush (A High)" in description

    def test_get_hand_description_royal_flush(self):
        """Test royal flush description."""
        hand = HandRanking(
            hand_type=HandType.ROYAL_FLUSH,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ks"),
                Card.from_string("Qs"),
                Card.from_string("Js"),
                Card.from_string("Ts"),
            ],
        )

        description = hand.get_hand_description()
        assert "♠ Royal Flush" in description


class TestHandRankingRepresentation:
    """Test HandRanking string and dictionary representation."""

    def test_to_dict(self):
        """Test converting hand ranking to dictionary."""
        hand = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[13, 12],
            royalty_bonus=2,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )

        hand_dict = hand.to_dict()

        assert hand_dict["hand_type"]["value"] == 1
        assert hand_dict["hand_type"]["name"] == "Pair"
        assert hand_dict["strength_value"] == 14
        assert hand_dict["kickers"] == [13, 12]
        assert hand_dict["royalty_bonus"] == 2
        assert hand_dict["total_value"] == 16
        assert hand_dict["cards"] == ["As", "Ah", "Kc"]
        assert "Pair of As" in hand_dict["description"]
        assert hand_dict["has_royalty"] == True
        assert hand_dict["is_made_hand"] == True
        assert hand_dict["is_premium_hand"] == False
        assert hand_dict["is_monster_hand"] == False

    def test_str_method_no_royalty(self):
        """Test __str__ method without royalty."""
        hand = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )

        hand_str = str(hand)
        assert "Pair of As" in hand_str
        assert "royalty" not in hand_str

    def test_str_method_with_royalty(self):
        """Test __str__ method with royalty."""
        hand = HandRanking(
            hand_type=HandType.FLUSH,
            strength_value=14,
            kickers=[],
            royalty_bonus=4,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ks"),
                Card.from_string("Qs"),
                Card.from_string("Js"),
                Card.from_string("9s"),
            ],
        )

        hand_str = str(hand)
        assert "Flush" in hand_str
        assert "+4 royalty" in hand_str


class TestHandRankingEdgeCases:
    """Test HandRanking edge cases and error conditions."""

    def test_hand_ranking_equality(self):
        """Test hand ranking equality."""
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

        hand1 = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[13],
            royalty_bonus=0,
            cards=cards1,
        )

        hand2 = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[13],
            royalty_bonus=0,
            cards=cards2,
        )

        # Different card objects but same values
        assert hand1.ties_with(hand2)

    def test_hand_ranking_hashable(self):
        """Test that hand rankings can be used in sets and dicts."""
        hand = HandRanking(
            hand_type=HandType.PAIR,
            strength_value=14,
            kickers=[],
            royalty_bonus=0,
            cards=[
                Card.from_string("As"),
                Card.from_string("Ah"),
                Card.from_string("Kc"),
            ],
        )

        # Can be used in sets
        hand_set = {hand}
        assert len(hand_set) == 1

        # Can be used as dict keys
        hand_dict = {hand: "pair of aces"}
        assert len(hand_dict) == 1
