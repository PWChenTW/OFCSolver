"""
Unit tests for Hand value object.
"""

import pytest

from src.domain.value_objects.card import Card, Rank, Suit
from src.domain.value_objects.card_position import CardPosition
from src.domain.value_objects.hand import (
    Hand,
    HandValidationError,
    InvalidCardPlacementError,
)


class TestHandCreation:
    """Test Hand creation and validation."""

    def test_empty_hand_creation(self):
        """Test creating an empty hand."""
        hand = Hand.empty()
        assert len(hand.top_row) == 0
        assert len(hand.middle_row) == 0
        assert len(hand.bottom_row) == 0
        assert len(hand.hand_cards) == 0
        assert not hand.is_complete()

    def test_hand_from_cards(self):
        """Test creating hand with cards in hand."""
        cards = [Card.from_string("As"), Card.from_string("Kh"), Card.from_string("Qc")]
        hand = Hand.from_cards(cards)

        assert len(hand.hand_cards) == 3
        assert len(hand.top_row) == 0
        assert len(hand.middle_row) == 0
        assert len(hand.bottom_row) == 0
        assert hand.hand_cards == cards

    def test_hand_from_layout(self):
        """Test creating hand from explicit layout."""
        top = [Card.from_string("As"), Card.from_string("Kh")]
        middle = [Card.from_string("Qc"), Card.from_string("Jd")]
        bottom = [Card.from_string("Ts"), Card.from_string("9h")]
        hand_cards = [Card.from_string("8c")]

        hand = Hand.from_layout(top, middle, bottom, hand_cards)

        assert hand.top_row == top
        assert hand.middle_row == middle
        assert hand.bottom_row == bottom
        assert hand.hand_cards == hand_cards

    def test_hand_validation_row_size_limits(self):
        """Test hand validation for row size limits."""
        # Too many cards in top row
        with pytest.raises(
            HandValidationError, match="Top row cannot have more than 3 cards"
        ):
            Hand.from_layout(
                top=[
                    Card.from_string("As"),
                    Card.from_string("Kh"),
                    Card.from_string("Qc"),
                    Card.from_string("Jd"),
                ],  # 4 cards
                middle=[],
                bottom=[],
            )

        # Too many cards in middle row
        with pytest.raises(
            HandValidationError, match="Middle row cannot have more than 5 cards"
        ):
            Hand.from_layout(
                top=[],
                middle=[
                    Card.from_string("As"),
                    Card.from_string("Kh"),
                    Card.from_string("Qc"),
                    Card.from_string("Jd"),
                    Card.from_string("Ts"),
                    Card.from_string("9h"),
                ],  # 6 cards
                bottom=[],
            )

        # Too many cards in bottom row
        with pytest.raises(
            HandValidationError, match="Bottom row cannot have more than 5 cards"
        ):
            Hand.from_layout(
                top=[],
                middle=[],
                bottom=[
                    Card.from_string("As"),
                    Card.from_string("Kh"),
                    Card.from_string("Qc"),
                    Card.from_string("Jd"),
                    Card.from_string("Ts"),
                    Card.from_string("9h"),
                ],  # 6 cards
            )

    def test_hand_validation_duplicate_cards(self):
        """Test hand validation for duplicate cards."""
        duplicate_card = Card.from_string("As")

        with pytest.raises(HandValidationError, match="Hand contains duplicate cards"):
            Hand.from_layout(
                top=[duplicate_card],
                middle=[duplicate_card],  # Same card in two places
                bottom=[],
            )

    def test_hand_validation_too_many_cards(self):
        """Test hand validation for too many total cards."""
        # Create 14 cards (exceeds OFC limit of 13)
        cards = [Card.from_string(f"{rank}s") for rank in "23456789TJQKA"] + [
            Card.from_string("2h")
        ]

        with pytest.raises(
            HandValidationError, match="Cannot create hand with more than 13 cards"
        ):
            Hand.from_cards(cards)

    def test_hand_from_cards_too_many(self):
        """Test creating hand from too many cards."""
        cards = [Card.from_string(f"{rank}s") for rank in "23456789TJQKA"] + [
            Card.from_string("2h")
        ]

        with pytest.raises(
            HandValidationError, match="Cannot create hand with more than 13 cards"
        ):
            Hand.from_cards(cards)


class TestHandProperties:
    """Test Hand property methods."""

    def test_is_complete(self):
        """Test hand completion checking."""
        # Incomplete hand
        hand = Hand.from_layout(
            top=[Card.from_string("As"), Card.from_string("Kh")],  # Only 2 cards
            middle=[Card.from_string("Qc")],  # Only 1 card
            bottom=[],
        )
        assert not hand.is_complete()

        # Complete hand
        complete_hand = Hand.from_layout(
            top=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
            middle=[
                Card.from_string("Jd"),
                Card.from_string("Ts"),
                Card.from_string("9h"),
                Card.from_string("8c"),
                Card.from_string("7d"),
            ],
            bottom=[
                Card.from_string("6s"),
                Card.from_string("5h"),
                Card.from_string("4c"),
                Card.from_string("3d"),
                Card.from_string("2s"),
            ],
        )
        assert complete_hand.is_complete()

    def test_is_valid_for_completion(self):
        """Test validation for completion potential."""
        # Valid - total 13 cards
        hand = Hand.from_layout(
            top=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
            middle=[Card.from_string("Jd"), Card.from_string("Ts")],
            bottom=[Card.from_string("9h")],
            hand=[Card.from_string(f"{rank}s") for rank in "876543"],  # 7 more cards
        )
        assert hand.is_valid_for_completion()

        # Still valid with fewer cards
        small_hand = Hand.from_layout(
            top=[Card.from_string("As")],
            middle=[],
            bottom=[],
            hand=[Card.from_string("Kh")],
        )
        assert small_hand.is_valid_for_completion()

    def test_get_available_positions(self):
        """Test getting available positions."""
        # All positions available
        empty_hand = Hand.empty()
        positions = empty_hand.get_available_positions()
        assert CardPosition.TOP in positions
        assert CardPosition.MIDDLE in positions
        assert CardPosition.BOTTOM in positions

        # Top full
        hand_top_full = Hand.from_layout(
            top=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
            middle=[],
            bottom=[],
        )
        positions = hand_top_full.get_available_positions()
        assert CardPosition.TOP not in positions
        assert CardPosition.MIDDLE in positions
        assert CardPosition.BOTTOM in positions

        # All full
        complete_hand = Hand.from_layout(
            top=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
            middle=[
                Card.from_string("Jd"),
                Card.from_string("Ts"),
                Card.from_string("9h"),
                Card.from_string("8c"),
                Card.from_string("7d"),
            ],
            bottom=[
                Card.from_string("6s"),
                Card.from_string("5h"),
                Card.from_string("4c"),
                Card.from_string("3d"),
                Card.from_string("2s"),
            ],
        )
        positions = complete_hand.get_available_positions()
        assert len(positions) == 0

    def test_can_place_card(self):
        """Test checking if cards can be placed."""
        hand = Hand.from_layout(
            top=[Card.from_string("As"), Card.from_string("Kh")],  # 2/3 cards
            middle=[Card.from_string("Qc")],  # 1/5 cards
            bottom=[],  # 0/5 cards
        )

        assert hand.can_place_card(CardPosition.TOP)  # Has space
        assert hand.can_place_card(CardPosition.MIDDLE)  # Has space
        assert hand.can_place_card(CardPosition.BOTTOM)  # Has space

        # Full top row
        hand_top_full = Hand.from_layout(
            top=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
            middle=[],
            bottom=[],
        )
        assert not hand_top_full.can_place_card(CardPosition.TOP)


class TestHandCardPlacement:
    """Test Hand card placement operations."""

    def test_place_card_success(self):
        """Test successful card placement."""
        card_to_place = Card.from_string("As")
        hand = Hand.from_cards([card_to_place, Card.from_string("Kh")])

        new_hand = hand.place_card(card_to_place, CardPosition.TOP)

        assert card_to_place in new_hand.top_row
        assert card_to_place not in new_hand.hand_cards
        assert len(new_hand.hand_cards) == 1
        assert len(new_hand.top_row) == 1

    def test_place_card_not_available(self):
        """Test placing card that's not in hand."""
        hand = Hand.from_cards([Card.from_string("Kh")])
        unavailable_card = Card.from_string("As")

        with pytest.raises(
            InvalidCardPlacementError, match="Card As is not available to place"
        ):
            hand.place_card(unavailable_card, CardPosition.TOP)

    def test_place_card_position_full(self):
        """Test placing card in full position."""
        card_to_place = Card.from_string("2s")
        hand = Hand.from_layout(
            top=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],  # Full
            middle=[],
            bottom=[],
            hand=[card_to_place],
        )

        with pytest.raises(
            InvalidCardPlacementError, match="Cannot place card in top - position full"
        ):
            hand.place_card(card_to_place, CardPosition.TOP)

    def test_place_cards_multiple(self):
        """Test placing multiple cards at once."""
        card1 = Card.from_string("As")
        card2 = Card.from_string("Kh")
        card3 = Card.from_string("Qc")

        hand = Hand.from_cards([card1, card2, card3])

        placements = [
            (card1, CardPosition.TOP),
            (card2, CardPosition.MIDDLE),
            (card3, CardPosition.BOTTOM),
        ]

        new_hand = hand.place_cards(placements)

        assert card1 in new_hand.top_row
        assert card2 in new_hand.middle_row
        assert card3 in new_hand.bottom_row
        assert len(new_hand.hand_cards) == 0

    def test_remove_card_success(self):
        """Test successful card removal."""
        card_to_remove = Card.from_string("As")
        hand = Hand.from_layout(
            top=[card_to_remove, Card.from_string("Kh")],
            middle=[],
            bottom=[],
            hand=[Card.from_string("Qc")],
        )

        new_hand = hand.remove_card(card_to_remove)

        assert card_to_remove not in new_hand.top_row
        assert card_to_remove in new_hand.hand_cards
        assert len(new_hand.top_row) == 1
        assert len(new_hand.hand_cards) == 2

    def test_remove_card_not_found(self):
        """Test removing card that's not in any row."""
        hand = Hand.from_layout(
            top=[Card.from_string("Kh")],
            middle=[],
            bottom=[],
            hand=[Card.from_string("Qc")],
        )

        missing_card = Card.from_string("As")

        with pytest.raises(
            InvalidCardPlacementError, match="Card As not found in any row"
        ):
            hand.remove_card(missing_card)


class TestHandUtilityMethods:
    """Test Hand utility and information methods."""

    def test_get_all_cards(self):
        """Test getting all cards in hand."""
        top_cards = [Card.from_string("As"), Card.from_string("Kh")]
        middle_cards = [Card.from_string("Qc")]
        bottom_cards = [Card.from_string("Jd")]
        hand_cards = [Card.from_string("Ts")]

        hand = Hand.from_layout(top_cards, middle_cards, bottom_cards, hand_cards)
        all_cards = hand.get_all_cards()

        assert len(all_cards) == 5
        for card in top_cards + middle_cards + bottom_cards + hand_cards:
            assert card in all_cards

    def test_get_all_placed_cards(self):
        """Test getting only placed cards."""
        top_cards = [Card.from_string("As"), Card.from_string("Kh")]
        middle_cards = [Card.from_string("Qc")]
        bottom_cards = [Card.from_string("Jd")]
        hand_cards = [Card.from_string("Ts")]

        hand = Hand.from_layout(top_cards, middle_cards, bottom_cards, hand_cards)
        placed_cards = hand.get_all_placed_cards()

        assert len(placed_cards) == 4
        for card in top_cards + middle_cards + bottom_cards:
            assert card in placed_cards
        assert hand_cards[0] not in placed_cards

    def test_get_cards_by_position(self):
        """Test getting cards by specific position."""
        top_cards = [Card.from_string("As"), Card.from_string("Kh")]
        middle_cards = [Card.from_string("Qc")]
        bottom_cards = [Card.from_string("Jd")]

        hand = Hand.from_layout(top_cards, middle_cards, bottom_cards)

        assert hand.get_cards_by_position(CardPosition.TOP) == top_cards
        assert hand.get_cards_by_position(CardPosition.MIDDLE) == middle_cards
        assert hand.get_cards_by_position(CardPosition.BOTTOM) == bottom_cards

        with pytest.raises(ValueError, match="Invalid position"):
            hand.get_cards_by_position("invalid")

    def test_count_cards_in_position(self):
        """Test counting cards in positions."""
        hand = Hand.from_layout(
            top=[Card.from_string("As"), Card.from_string("Kh")],  # 2 cards
            middle=[Card.from_string("Qc")],  # 1 card
            bottom=[],  # 0 cards
        )

        assert hand.count_cards_in_position(CardPosition.TOP) == 2
        assert hand.count_cards_in_position(CardPosition.MIDDLE) == 1
        assert hand.count_cards_in_position(CardPosition.BOTTOM) == 0

    def test_position_status_checks(self):
        """Test position status checking methods."""
        hand = Hand.from_layout(
            top=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],  # Full
            middle=[Card.from_string("Jd")],  # Partial
            bottom=[],  # Empty
        )

        # Full position
        assert hand.is_position_full(CardPosition.TOP)
        assert not hand.is_position_empty(CardPosition.TOP)

        # Partial position
        assert not hand.is_position_full(CardPosition.MIDDLE)
        assert not hand.is_position_empty(CardPosition.MIDDLE)

        # Empty position
        assert not hand.is_position_full(CardPosition.BOTTOM)
        assert hand.is_position_empty(CardPosition.BOTTOM)

    def test_get_completion_progress(self):
        """Test getting completion progress."""
        hand = Hand.from_layout(
            top=[Card.from_string("As"), Card.from_string("Kh")],  # 2/3
            middle=[Card.from_string("Qc")],  # 1/5
            bottom=[],  # 0/5
        )

        progress = hand.get_completion_progress()

        assert progress[CardPosition.TOP]["current"] == 2
        assert progress[CardPosition.TOP]["max"] == 3
        assert not progress[CardPosition.TOP]["complete"]

        assert progress[CardPosition.MIDDLE]["current"] == 1
        assert progress[CardPosition.MIDDLE]["max"] == 5
        assert not progress[CardPosition.MIDDLE]["complete"]

        assert progress[CardPosition.BOTTOM]["current"] == 0
        assert progress[CardPosition.BOTTOM]["max"] == 5
        assert not progress[CardPosition.BOTTOM]["complete"]


class TestHandStringRepresentation:
    """Test Hand string and dictionary representation."""

    def test_to_dict(self):
        """Test converting hand to dictionary."""
        hand = Hand.from_layout(
            top=[Card.from_string("As"), Card.from_string("Kh")],
            middle=[Card.from_string("Qc")],
            bottom=[],
            hand=[Card.from_string("Jd")],
        )

        hand_dict = hand.to_dict()

        assert hand_dict["top_row"] == ["As", "Kh"]
        assert hand_dict["middle_row"] == ["Qc"]
        assert hand_dict["bottom_row"] == []
        assert hand_dict["hand_cards"] == ["Jd"]
        assert hand_dict["is_complete"] == False
        assert "completion_progress" in hand_dict

    def test_to_string(self):
        """Test converting hand to string representation."""
        hand = Hand.from_layout(
            top=[Card.from_string("As"), Card.from_string("Kh")],
            middle=[Card.from_string("Qc")],
            bottom=[],
            hand=[Card.from_string("Jd")],
        )

        hand_str = hand.to_string()

        assert "Top: As Kh" in hand_str
        assert "Mid: Qc" in hand_str
        assert "Bot: (empty)" in hand_str
        assert "Hand: Jd" in hand_str

    def test_str_method(self):
        """Test __str__ method."""
        hand = Hand.from_layout(top=[Card.from_string("As")], middle=[], bottom=[])

        hand_str = str(hand)
        assert "Top: As" in hand_str
        assert "Mid: (empty)" in hand_str
        assert "Bot: (empty)" in hand_str

    def test_len_method(self):
        """Test __len__ method."""
        hand = Hand.from_layout(
            top=[Card.from_string("As"), Card.from_string("Kh")],
            middle=[Card.from_string("Qc")],
            bottom=[],
            hand=[Card.from_string("Jd"), Card.from_string("Ts")],
        )

        assert len(hand) == 5  # Total cards

    def test_normalize_for_comparison(self):
        """Test normalizing hand for comparison."""
        hand = Hand.from_layout(
            top=[Card.from_string("Kh"), Card.from_string("As")],  # Unsorted
            middle=[Card.from_string("Qc")],
            bottom=[],
            hand=[Card.from_string("Jd")],
        )

        normalized = hand.normalize_for_comparison()

        # Should be sorted
        assert normalized["top"] == ["As", "Kh"]
        assert normalized["middle"] == ["Qc"]
        assert normalized["bottom"] == []
        assert normalized["hand"] == ["Jd"]


class TestHandOFCRules:
    """Test OFC-specific hand validation."""

    def test_is_fouled_placeholder(self):
        """Test fouled checking (placeholder implementation)."""
        # Currently returns False as placeholder
        hand = Hand.from_layout(
            top=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
            middle=[
                Card.from_string("Jd"),
                Card.from_string("Ts"),
                Card.from_string("9h"),
                Card.from_string("8c"),
                Card.from_string("7d"),
            ],
            bottom=[
                Card.from_string("6s"),
                Card.from_string("5h"),
                Card.from_string("4c"),
                Card.from_string("3d"),
                Card.from_string("2s"),
            ],
        )

        # Placeholder implementation returns False
        assert not hand.is_fouled()

    def test_validate_ofc_rules(self):
        """Test OFC rules validation."""
        hand = Hand.from_layout(
            top=[
                Card.from_string("As"),
                Card.from_string("Kh"),
                Card.from_string("Qc"),
            ],
            middle=[
                Card.from_string("Jd"),
                Card.from_string("Ts"),
                Card.from_string("9h"),
                Card.from_string("8c"),
                Card.from_string("7d"),
            ],
            bottom=[
                Card.from_string("6s"),
                Card.from_string("5h"),
                Card.from_string("4c"),
                Card.from_string("3d"),
                Card.from_string("2s"),
            ],
        )

        # Placeholder implementation returns True (not fouled)
        assert hand.validate_ofc_rules()


class TestHandImmutability:
    """Test Hand immutability."""

    def test_hand_immutable(self):
        """Test that hand operations create new instances."""
        original_hand = Hand.from_cards(
            [Card.from_string("As"), Card.from_string("Kh")]
        )

        # Place card creates new hand
        new_hand = original_hand.place_card(Card.from_string("As"), CardPosition.TOP)

        # Original hand unchanged
        assert len(original_hand.top_row) == 0
        assert len(original_hand.hand_cards) == 2

        # New hand has changes
        assert len(new_hand.top_row) == 1
        assert len(new_hand.hand_cards) == 1

        # Different objects
        assert original_hand is not new_hand
