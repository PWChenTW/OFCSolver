"""
Unit tests for Card value object.
"""

import pytest

from src.domain.value_objects.card import Card, Rank, Suit


class TestRank:
    """Test Rank enum functionality."""

    def test_rank_creation(self):
        """Test rank creation and properties."""
        rank = Rank.ACE
        assert rank.numeric_value == 14
        assert rank.symbol == "A"
        assert str(rank) == "A"

    def test_rank_comparison(self):
        """Test rank comparison operations."""
        assert Rank.TWO < Rank.ACE
        assert Rank.KING < Rank.ACE
        assert Rank.JACK <= Rank.QUEEN
        assert Rank.ACE > Rank.KING
        assert Rank.QUEEN >= Rank.JACK
        assert Rank.TEN == Rank.TEN

    def test_rank_from_symbol(self):
        """Test creating rank from symbol string."""
        assert Rank.from_symbol("A") == Rank.ACE
        assert Rank.from_symbol("K") == Rank.KING
        assert Rank.from_symbol("2") == Rank.TWO
        assert Rank.from_symbol("T") == Rank.TEN

        # Case insensitive
        assert Rank.from_symbol("a") == Rank.ACE
        assert Rank.from_symbol("k") == Rank.KING

    def test_rank_from_symbol_invalid(self):
        """Test invalid rank symbol raises error."""
        with pytest.raises(ValueError, match="Invalid rank symbol"):
            Rank.from_symbol("X")

        with pytest.raises(ValueError, match="Invalid rank symbol"):
            Rank.from_symbol("1")

    def test_all_ranks(self):
        """Test getting all ranks in order."""
        ranks = Rank.all_ranks()
        assert len(ranks) == 13
        assert ranks[0] == Rank.TWO
        assert ranks[-1] == Rank.ACE

        # Verify order
        for i in range(len(ranks) - 1):
            assert ranks[i] < ranks[i + 1]


class TestSuit:
    """Test Suit enum functionality."""

    def test_suit_creation(self):
        """Test suit creation and properties."""
        suit = Suit.SPADES
        assert suit.value == "s"
        assert str(suit) == "s"
        assert suit.symbol == "♠"

    def test_suit_properties(self):
        """Test suit color properties."""
        # Red suits
        assert Suit.HEARTS.is_red
        assert Suit.DIAMONDS.is_red
        assert not Suit.HEARTS.is_black
        assert not Suit.DIAMONDS.is_black

        # Black suits
        assert Suit.SPADES.is_black
        assert Suit.CLUBS.is_black
        assert not Suit.SPADES.is_red
        assert not Suit.CLUBS.is_red

    def test_all_suits(self):
        """Test all suits are present."""
        suits = list(Suit)
        assert len(suits) == 4
        assert Suit.SPADES in suits
        assert Suit.HEARTS in suits
        assert Suit.DIAMONDS in suits
        assert Suit.CLUBS in suits


class TestCard:
    """Test Card value object functionality."""

    def test_card_creation(self):
        """Test basic card creation."""
        card = Card(suit=Suit.SPADES, rank=Rank.ACE)
        assert card.suit == Suit.SPADES
        assert card.rank == Rank.ACE
        assert card.numeric_rank == 14

    def test_card_creation_validation(self):
        """Test card creation with invalid parameters."""
        with pytest.raises(TypeError):
            Card(suit="invalid", rank=Rank.ACE)

        with pytest.raises(TypeError):
            Card(suit=Suit.SPADES, rank="invalid")

    def test_card_from_string(self):
        """Test creating card from string representation."""
        # Test valid cards
        card = Card.from_string("As")
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES

        card = Card.from_string("Kh")
        assert card.rank == Rank.KING
        assert card.suit == Suit.HEARTS

        card = Card.from_string("2c")
        assert card.rank == Rank.TWO
        assert card.suit == Suit.CLUBS

        card = Card.from_string("Td")
        assert card.rank == Rank.TEN
        assert card.suit == Suit.DIAMONDS

    def test_card_from_string_case_insensitive(self):
        """Test card from string is case insensitive."""
        card1 = Card.from_string("AS")
        card2 = Card.from_string("as")
        card3 = Card.from_string("As")
        card4 = Card.from_string("aS")

        assert card1 == card2 == card3 == card4

    def test_card_from_string_invalid(self):
        """Test invalid card strings raise errors."""
        # Wrong length
        with pytest.raises(ValueError, match="must be 2 characters"):
            Card.from_string("A")

        with pytest.raises(ValueError, match="must be 2 characters"):
            Card.from_string("Ace")

        # Invalid rank
        with pytest.raises(ValueError, match="Invalid rank symbol"):
            Card.from_string("Xs")

        # Invalid suit
        with pytest.raises(ValueError, match="Invalid suit symbol"):
            Card.from_string("Ax")

    def test_card_to_string(self):
        """Test converting card to string representation."""
        card = Card(suit=Suit.SPADES, rank=Rank.ACE)
        assert str(card) == "As"

        card = Card(suit=Suit.HEARTS, rank=Rank.KING)
        assert str(card) == "Kh"

        card = Card(suit=Suit.CLUBS, rank=Rank.TWO)
        assert str(card) == "2c"

        card = Card(suit=Suit.DIAMONDS, rank=Rank.TEN)
        assert str(card) == "Td"

    def test_card_properties(self):
        """Test card property methods."""
        # Red cards
        red_card = Card(suit=Suit.HEARTS, rank=Rank.ACE)
        assert red_card.is_red
        assert not red_card.is_black

        # Black cards
        black_card = Card(suit=Suit.SPADES, rank=Rank.ACE)
        assert black_card.is_black
        assert not black_card.is_red

        # Face cards
        face_card = Card(suit=Suit.SPADES, rank=Rank.JACK)
        assert face_card.is_face_card

        non_face_card = Card(suit=Suit.SPADES, rank=Rank.TWO)
        assert not non_face_card.is_face_card

        # Ace
        ace_card = Card(suit=Suit.SPADES, rank=Rank.ACE)
        assert ace_card.is_ace

        non_ace_card = Card(suit=Suit.SPADES, rank=Rank.KING)
        assert not non_ace_card.is_ace

    def test_card_comparison(self):
        """Test card comparison operations."""
        # Same rank, different suit
        as_card = Card(suit=Suit.SPADES, rank=Rank.ACE)
        ah_card = Card(suit=Suit.HEARTS, rank=Rank.ACE)

        # Different rank
        ks_card = Card(suit=Suit.SPADES, rank=Rank.KING)

        # Test rank comparison
        assert ks_card < as_card
        assert as_card > ks_card

        # Test suit comparison for same rank (spades > hearts in our ordering)
        assert as_card > ah_card
        assert ah_card < as_card

        # Test equality
        as_card2 = Card(suit=Suit.SPADES, rank=Rank.ACE)
        assert as_card == as_card2
        assert not (as_card != as_card2)

    def test_card_consecutive(self):
        """Test consecutive card checking."""
        card1 = Card(suit=Suit.SPADES, rank=Rank.FIVE)
        card2 = Card(suit=Suit.HEARTS, rank=Rank.SIX)
        card3 = Card(suit=Suit.CLUBS, rank=Rank.EIGHT)

        assert card1.is_consecutive(card2)
        assert card2.is_consecutive(card1)
        assert not card1.is_consecutive(card3)

    def test_card_same_suit(self):
        """Test same suit checking."""
        card1 = Card(suit=Suit.SPADES, rank=Rank.ACE)
        card2 = Card(suit=Suit.SPADES, rank=Rank.KING)
        card3 = Card(suit=Suit.HEARTS, rank=Rank.ACE)

        assert card1.is_same_suit(card2)
        assert not card1.is_same_suit(card3)

    def test_card_same_rank(self):
        """Test same rank checking."""
        card1 = Card(suit=Suit.SPADES, rank=Rank.ACE)
        card2 = Card(suit=Suit.HEARTS, rank=Rank.ACE)
        card3 = Card(suit=Suit.SPADES, rank=Rank.KING)

        assert card1.is_same_rank(card2)
        assert not card1.is_same_rank(card3)

    def test_create_deck(self):
        """Test creating a full deck."""
        deck = Card.create_deck()
        assert len(deck) == 52

        # Check all combinations exist
        expected_cards = []
        for suit in Suit:
            for rank in Rank:
                expected_cards.append(Card(suit=suit, rank=rank))

        assert len(deck) == len(expected_cards)

        # Check no duplicates
        assert len(set(deck)) == 52

    def test_parse_cards(self):
        """Test parsing multiple cards from string."""
        cards = Card.parse_cards("As Kh 2c Td")
        assert len(cards) == 4
        assert cards[0] == Card.from_string("As")
        assert cards[1] == Card.from_string("Kh")
        assert cards[2] == Card.from_string("2c")
        assert cards[3] == Card.from_string("Td")

        # Empty string
        cards = Card.parse_cards("")
        assert len(cards) == 0

        # Single card
        cards = Card.parse_cards("As")
        assert len(cards) == 1
        assert cards[0] == Card.from_string("As")

    def test_cards_to_string(self):
        """Test converting cards list to string."""
        cards = [Card.from_string("As"), Card.from_string("Kh"), Card.from_string("2c")]
        result = Card.cards_to_string(cards)
        assert result == "As Kh 2c"

        # Empty list
        assert Card.cards_to_string([]) == ""

    def test_group_by_suit(self):
        """Test grouping cards by suit."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("Ah"),
            Card.from_string("2c"),
        ]

        groups = Card.group_by_suit(cards)
        assert len(groups[Suit.SPADES]) == 2
        assert len(groups[Suit.HEARTS]) == 1
        assert len(groups[Suit.CLUBS]) == 1
        assert len(groups[Suit.DIAMONDS]) == 0

    def test_group_by_rank(self):
        """Test grouping cards by rank."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Ks"),
            Card.from_string("2c"),
        ]

        groups = Card.group_by_rank(cards)
        assert len(groups[Rank.ACE]) == 2
        assert len(groups[Rank.KING]) == 1
        assert len(groups[Rank.TWO]) == 1
        assert Rank.QUEEN not in groups  # No Queens in the list

    def test_sort_by_rank(self):
        """Test sorting cards by rank."""
        cards = [
            Card.from_string("2s"),
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("5h"),
        ]

        # Descending (default)
        sorted_cards = Card.sort_by_rank(cards)
        ranks = [card.rank for card in sorted_cards]
        assert ranks == [Rank.ACE, Rank.KING, Rank.FIVE, Rank.TWO]

        # Ascending
        sorted_cards = Card.sort_by_rank(cards, descending=False)
        ranks = [card.rank for card in sorted_cards]
        assert ranks == [Rank.TWO, Rank.FIVE, Rank.KING, Rank.ACE]

    def test_sort_by_suit(self):
        """Test sorting cards by suit."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Ac"),
            Card.from_string("Ad"),
        ]

        sorted_cards = Card.sort_by_suit(cards)
        suits = [card.suit for card in sorted_cards]
        # Clubs=1, Diamonds=2, Hearts=3, Spades=4
        assert suits == [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]

    def test_validate_no_duplicates(self):
        """Test duplicate validation."""
        # No duplicates
        cards = [Card.from_string("As"), Card.from_string("Kh"), Card.from_string("2c")]
        assert Card.validate_no_duplicates(cards)

        # With duplicates
        cards_with_dups = [
            Card.from_string("As"),
            Card.from_string("As"),  # Duplicate
            Card.from_string("Kh"),
        ]
        assert not Card.validate_no_duplicates(cards_with_dups)

    def test_get_missing_cards(self):
        """Test getting missing cards from deck."""
        provided_cards = [Card.from_string("As"), Card.from_string("Kh")]
        missing_cards = Card.get_missing_cards(provided_cards)

        assert len(missing_cards) == 50  # 52 - 2
        assert Card.from_string("As") not in missing_cards
        assert Card.from_string("Kh") not in missing_cards

        # Full deck should have no missing cards
        full_deck = Card.create_deck()
        missing = Card.get_missing_cards(full_deck)
        assert len(missing) == 0

    def test_card_hashable(self):
        """Test that cards are hashable and can be used in sets."""
        card1 = Card.from_string("As")
        card2 = Card.from_string("As")
        card3 = Card.from_string("Kh")

        # Same cards should have same hash
        assert hash(card1) == hash(card2)

        # Can be used in sets
        card_set = {card1, card2, card3}
        assert len(card_set) == 2  # card1 and card2 are the same

        # Can be used as dict keys
        card_dict = {card1: "ace", card3: "king"}
        assert len(card_dict) == 2

    def test_card_immutable(self):
        """Test that cards are immutable."""
        card = Card.from_string("As")

        # Cannot modify attributes (frozen dataclass)
        with pytest.raises(AttributeError):
            card.suit = Suit.HEARTS

        with pytest.raises(AttributeError):
            card.rank = Rank.KING
