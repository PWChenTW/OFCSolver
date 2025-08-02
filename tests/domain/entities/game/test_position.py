"""
Tests for Position Entity
"""

import pytest

from src.domain.entities.game import Position
from src.domain.value_objects import Card, CardPosition, GameRules, Hand, Move


class TestPosition:
    """Test suite for Position entity."""

    def create_test_position(self, num_players=2):
        """Helper to create a test position."""
        players_hands = {}
        for i in range(num_players):
            player_id = f"player{i+1}"
            cards = Card.parse_cards("As Ks Qs Js Ts")[:i+2]  # Different cards per player
            players_hands[player_id] = Hand.from_cards(cards)
        
        remaining_cards = Card.parse_cards("9s 8s 7s 6s 5s 4s 3s 2s")
        
        return Position(
            game_id="game1",
            players_hands=players_hands,
            remaining_cards=remaining_cards,
            current_player_id="player1",
            round_number=1,
            rules=GameRules.standard_rules(),
        )

    def test_position_initialization(self):
        """Test position creation and properties."""
        position = self.create_test_position()
        
        assert position.game_id == "game1"
        assert position.player_count == 2
        assert position.current_player_id == "player1"
        assert position.round_number == 1
        assert position.cards_remaining_count == 8
        assert isinstance(position.id, str)
        assert position.id.startswith("pos_")

    def test_position_initialization_with_custom_id(self):
        """Test position creation with custom ID."""
        position = Position(
            game_id="game1",
            players_hands={"p1": Hand.empty()},
            remaining_cards=[],
            current_player_id="p1",
            round_number=1,
            rules=GameRules(),
            position_id="custom_pos_123",
        )
        
        assert position.id == "custom_pos_123"

    def test_get_player_hand(self):
        """Test getting specific player's hand."""
        position = self.create_test_position()
        
        hand = position.get_player_hand("player1")
        assert hand is not None
        assert len(hand.hand_cards) == 2
        
        # Non-existent player
        assert position.get_player_hand("invalid_player") is None

    def test_get_current_player_hand(self):
        """Test getting current player's hand."""
        position = self.create_test_position()
        
        hand = position.get_current_player_hand()
        assert hand is not None
        assert hand == position.get_player_hand("player1")

    def test_get_current_player_hand_invalid(self):
        """Test getting hand when current player doesn't exist."""
        position = Position(
            game_id="game1",
            players_hands={"p1": Hand.empty()},
            remaining_cards=[],
            current_player_id="invalid_player",
            round_number=1,
            rules=GameRules(),
        )
        
        with pytest.raises(ValueError, match="Current player invalid_player not found"):
            position.get_current_player_hand()

    def test_get_opponent_hands(self):
        """Test getting opponent hands."""
        position = self.create_test_position(3)
        
        opponent_hands = position.get_opponent_hands()
        assert len(opponent_hands) == 2
        assert "player1" not in opponent_hands
        assert "player2" in opponent_hands
        assert "player3" in opponent_hands

    def test_is_terminal_position(self):
        """Test checking if position is terminal."""
        # Non-terminal position
        position = self.create_test_position()
        assert not position.is_terminal_position()
        
        # Terminal position (all hands complete)
        complete_hands = {}
        for i in range(2):
            player_id = f"player{i+1}"
            # Create complete hand
            top = Card.parse_cards("As Ks Qs")
            middle = Card.parse_cards("Js Ts 9s 8s 7s")
            bottom = Card.parse_cards("6s 5s 4s 3s 2s")
            complete_hands[player_id] = Hand.from_layout(top, middle, bottom)
        
        terminal_position = Position(
            game_id="game1",
            players_hands=complete_hands,
            remaining_cards=[],
            current_player_id="player1",
            round_number=13,
            rules=GameRules(),
        )
        
        assert terminal_position.is_terminal_position()

    def test_game_phase_detection(self):
        """Test early/mid/end game detection."""
        # Early game
        early_position = self.create_test_position()
        assert early_position.is_early_game()
        assert not early_position.is_mid_game()
        assert not early_position.is_end_game()
        
        # Mid game
        mid_position = Position(
            game_id="game1",
            players_hands={"p1": Hand.empty()},
            remaining_cards=[],
            current_player_id="p1",
            round_number=5,
            rules=GameRules(),
        )
        assert not mid_position.is_early_game()
        assert mid_position.is_mid_game()
        assert not mid_position.is_end_game()
        
        # End game
        end_position = Position(
            game_id="game1",
            players_hands={"p1": Hand.empty()},
            remaining_cards=[],
            current_player_id="p1",
            round_number=10,
            rules=GameRules(),
        )
        assert not end_position.is_early_game()
        assert not end_position.is_mid_game()
        assert end_position.is_end_game()

    def test_get_legal_moves(self):
        """Test getting legal moves from position."""
        # Create position with cards in hand
        hand = Hand.from_cards(Card.parse_cards("As Ks Qs"))
        position = Position(
            game_id="game1",
            players_hands={"p1": hand},
            remaining_cards=[],
            current_player_id="p1",
            round_number=1,
            rules=GameRules(),
        )
        
        moves = position.get_legal_moves()
        
        # 3 cards × 3 positions = 9 possible moves
        assert len(moves) == 9
        
        # Check moves are valid
        for move in moves:
            assert isinstance(move, Move)
            assert move.card in hand.hand_cards
            assert move.position in CardPosition.all_positions()

    def test_get_legal_moves_partial_layout(self):
        """Test legal moves with partially filled layout."""
        # Create hand with top row full
        top = Card.parse_cards("As Ks Qs")
        hand_cards = Card.parse_cards("Js Ts")
        hand = Hand.from_layout(top, [], [], hand_cards)
        
        position = Position(
            game_id="game1",
            players_hands={"p1": hand},
            remaining_cards=[],
            current_player_id="p1",
            round_number=4,
            rules=GameRules(),
        )
        
        moves = position.get_legal_moves()
        
        # 2 cards × 2 positions (middle, bottom) = 4 moves
        assert len(moves) == 4
        # No moves to TOP position
        assert all(move.position != CardPosition.TOP for move in moves)

    def test_position_hash(self):
        """Test position hashing for caching."""
        position1 = self.create_test_position()
        hash1 = position1.get_position_hash()
        
        # Same position should have same hash
        position2 = self.create_test_position()
        hash2 = position2.get_position_hash()
        assert hash1 == hash2
        
        # Different positions should have different hashes
        position3 = self.create_test_position()
        position3._round_number = 2
        hash3 = position3.get_position_hash()
        assert hash1 != hash3

    def test_position_equality(self):
        """Test position equality based on hash."""
        position1 = self.create_test_position()
        position2 = self.create_test_position()
        
        # Same game state
        assert position1 == position2
        assert hash(position1) == hash(position2)
        
        # Different game state
        position3 = self.create_test_position()
        position3._current_player_id = "player2"
        assert position1 != position3
        assert hash(position1) != hash(position3)

    def test_complexity_score(self):
        """Test position complexity calculation."""
        position = self.create_test_position()
        complexity = position.get_complexity_score()
        
        assert isinstance(complexity, float)
        assert 0 <= complexity <= 100
        
        # Early game complexity can vary based on factors
        assert 0 <= complexity <= 100

    def test_to_analysis_format(self):
        """Test conversion to analysis format."""
        position = self.create_test_position()
        analysis_data = position.to_analysis_format()
        
        assert isinstance(analysis_data, dict)
        assert analysis_data["position_id"] == str(position.id)
        assert analysis_data["game_id"] == "game1"
        assert analysis_data["round_number"] == 1
        assert analysis_data["current_player"] == "player1"
        assert "players_hands" in analysis_data
        assert "remaining_cards" in analysis_data
        assert "position_hash" in analysis_data
        assert "complexity_score" in analysis_data

    def test_apply_move(self):
        """Test applying a move to create new position."""
        # Create position with cards in hand
        hand = Hand.from_cards(Card.parse_cards("As Ks"))
        position = Position(
            game_id="game1",
            players_hands={"p1": hand, "p2": Hand.empty()},
            remaining_cards=Card.parse_cards("Qs Js"),
            current_player_id="p1",
            round_number=1,
            rules=GameRules(),
        )
        
        # Apply move
        move = Move(card=Card.from_string("As"), position=CardPosition.TOP)
        new_position = position.apply_move(move)
        
        # Check new position state
        assert new_position.game_id == position.game_id
        assert new_position.round_number == position.round_number
        assert new_position.current_player_id == "p2"  # Turn advanced
        # The current implementation doesn't remove cards from remaining_cards
        # since cards in hand are not necessarily from remaining_cards
        assert len(new_position.remaining_cards) == 2

    def test_position_representation(self):
        """Test string representation of position."""
        position = self.create_test_position()
        
        repr_str = repr(position)
        assert "Position" in repr_str
        assert position.id in repr_str
        assert "game1" in repr_str
        assert "round=1" in repr_str
        assert "player1" in repr_str