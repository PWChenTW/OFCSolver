"""
Tests for Player Entity
"""

import pytest

from src.domain.entities.game.player import Player, PlayerStatus
from src.domain.exceptions import GameStateError, InvalidCardPlacementError
from src.domain.value_objects import Card, CardPosition


class TestPlayer:
    """Test suite for Player entity."""

    def test_player_initialization(self):
        """Test player creation and initial state."""
        player = Player("player1", "Alice")
        
        assert player.id == "player1"
        assert player.name == "Alice"
        assert player.status == PlayerStatus.ACTIVE
        assert player.total_cards_placed == 0
        assert not player.is_in_fantasy_land
        assert len(player.top_row) == 0
        assert len(player.middle_row) == 0
        assert len(player.bottom_row) == 0
        assert len(player.hand_cards) == 0

    def test_receive_initial_cards(self):
        """Test receiving initial 5 cards."""
        player = Player("player1", "Alice")
        cards = [
            Card.from_string("As"),
            Card.from_string("Ks"),
            Card.from_string("Qs"),
            Card.from_string("Js"),
            Card.from_string("Ts"),
        ]
        
        player.receive_initial_cards(cards)
        
        assert len(player.hand_cards) == 5
        assert all(card in player.hand_cards for card in cards)

    def test_receive_initial_cards_invalid_count(self):
        """Test receiving wrong number of initial cards."""
        player = Player("player1", "Alice")
        cards = [Card.from_string("As"), Card.from_string("Ks")]
        
        with pytest.raises(GameStateError, match="Initial deal must be exactly 5 cards"):
            player.receive_initial_cards(cards)

    def test_receive_initial_cards_already_has_cards(self):
        """Test receiving initial cards when player already has cards."""
        player = Player("player1", "Alice")
        player.receive_card(Card.from_string("As"))
        
        cards = Card.parse_cards("Ks Qs Js Ts 9s")
        
        with pytest.raises(GameStateError, match="Player already has cards"):
            player.receive_initial_cards(cards)

    def test_place_card_valid(self):
        """Test valid card placement."""
        player = Player("player1", "Alice")
        cards = Card.parse_cards("As Ks Qs Js Ts")
        player.receive_initial_cards(cards)
        
        # Place card in top row
        ace = Card.from_string("As")
        player.place_card(ace, CardPosition.TOP)
        
        assert len(player.top_row) == 1
        assert player.top_row[0] == ace
        assert len(player.hand_cards) == 4
        assert ace not in player.hand_cards
        assert player.has_placed_card_this_round()

    def test_place_card_invalid_position_full(self):
        """Test placing card in full position."""
        player = Player("player1", "Alice")
        
        # Fill top row (3 cards max)
        cards = Card.parse_cards("As Ks Qs")
        for card in cards:
            player.receive_card(card)
            player.place_card(card, CardPosition.TOP)
        
        # Try to place 4th card
        extra_card = Card.from_string("Js")
        player.receive_card(extra_card)
        
        with pytest.raises(InvalidCardPlacementError):
            player.place_card(extra_card, CardPosition.TOP)

    def test_place_card_not_in_hand(self):
        """Test placing card not in hand."""
        player = Player("player1", "Alice")
        card = Card.from_string("As")
        
        with pytest.raises(InvalidCardPlacementError):
            player.place_card(card, CardPosition.TOP)

    def test_can_place_card(self):
        """Test card placement validation."""
        player = Player("player1", "Alice")
        card = Card.from_string("As")
        player.receive_card(card)
        
        # Should be able to place in any empty row
        assert player.can_place_card(card, CardPosition.TOP)
        assert player.can_place_card(card, CardPosition.MIDDLE)
        assert player.can_place_card(card, CardPosition.BOTTOM)
        
        # Card not in hand
        other_card = Card.from_string("Ks")
        assert not player.can_place_card(other_card, CardPosition.TOP)

    def test_layout_complete(self):
        """Test checking if layout is complete."""
        player = Player("player1", "Alice")
        
        assert not player.is_layout_complete()
        
        # Place 13 cards total (3 top, 5 middle, 5 bottom)
        cards = Card.parse_cards("As Ks Qs Js Ts 9s 8s 7s 6s 5s 4s 3s 2s")
        
        # Top row - 3 cards
        for i in range(3):
            player.receive_card(cards[i])
            player.place_card(cards[i], CardPosition.TOP)
        
        # Middle row - 5 cards
        for i in range(3, 8):
            player.receive_card(cards[i])
            player.place_card(cards[i], CardPosition.MIDDLE)
        
        # Bottom row - 5 cards
        for i in range(8, 13):
            player.receive_card(cards[i])
            player.place_card(cards[i], CardPosition.BOTTOM)
        
        assert player.is_layout_complete()
        assert player.total_cards_placed == 13

    def test_get_available_positions(self):
        """Test getting available positions for card placement."""
        player = Player("player1", "Alice")
        
        # All positions available initially
        positions = player.get_available_positions()
        assert len(positions) == 3
        assert CardPosition.TOP in positions
        assert CardPosition.MIDDLE in positions
        assert CardPosition.BOTTOM in positions
        
        # Fill top row
        cards = Card.parse_cards("As Ks Qs")
        for card in cards:
            player.receive_card(card)
            player.place_card(card, CardPosition.TOP)
        
        # Top should no longer be available
        positions = player.get_available_positions()
        assert len(positions) == 2
        assert CardPosition.TOP not in positions
        assert CardPosition.MIDDLE in positions
        assert CardPosition.BOTTOM in positions

    def test_fantasy_land_state(self):
        """Test fantasy land state management."""
        player = Player("player1", "Alice")
        
        assert not player.is_in_fantasy_land
        assert player.status == PlayerStatus.ACTIVE
        
        # Enter fantasy land
        player.enter_fantasy_land()
        assert player.is_in_fantasy_land
        assert player.status == PlayerStatus.FANTASY_LAND
        
        # Exit fantasy land
        player.exit_fantasy_land()
        assert not player.is_in_fantasy_land
        assert player.status == PlayerStatus.ACTIVE

    def test_receive_fantasy_land_cards(self):
        """Test receiving cards in fantasy land mode."""
        player = Player("player1", "Alice")
        
        # Can't receive fantasy land cards if not in fantasy land
        cards = Card.parse_cards("As Ks Qs Js Ts 9s 8s 7s 6s 5s 4s 3s 2s")
        with pytest.raises(GameStateError, match="Player must be in fantasy land"):
            player.receive_fantasy_land_cards(cards)
        
        # Enter fantasy land and receive cards
        player.enter_fantasy_land()
        player.receive_fantasy_land_cards(cards)
        
        assert len(player.hand_cards) == 13
        assert all(card in player.hand_cards for card in cards)

    def test_round_state_management(self):
        """Test round state tracking."""
        player = Player("player1", "Alice")
        card = Card.from_string("As")
        
        # Initially hasn't placed card
        assert not player.has_placed_card_this_round()
        
        # Place a card
        player.receive_card(card)
        player.place_card(card, CardPosition.TOP)
        assert player.has_placed_card_this_round()
        
        # Start new round
        player.start_new_round()
        assert not player.has_placed_card_this_round()

    def test_get_row_cards(self):
        """Test getting cards from specific rows."""
        player = Player("player1", "Alice")
        
        # Place cards in different rows
        ace = Card.from_string("As")
        king = Card.from_string("Ks")
        queen = Card.from_string("Qs")
        
        player.receive_card(ace)
        player.place_card(ace, CardPosition.TOP)
        
        player.receive_card(king)
        player.place_card(king, CardPosition.MIDDLE)
        
        player.receive_card(queen)
        player.place_card(queen, CardPosition.BOTTOM)
        
        # Check each row
        assert player.get_row_cards(CardPosition.TOP) == [ace]
        assert player.get_row_cards(CardPosition.MIDDLE) == [king]
        assert player.get_row_cards(CardPosition.BOTTOM) == [queen]

    def test_player_representation(self):
        """Test string representation of player."""
        player = Player("player1", "Alice")
        
        repr_str = repr(player)
        assert "Player" in repr_str
        assert "player1" in repr_str
        assert "Alice" in repr_str
        assert "cards_placed=0" in repr_str
        assert "status=active" in repr_str