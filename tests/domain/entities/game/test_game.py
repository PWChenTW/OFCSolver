"""
Tests for Game Entity (Aggregate Root)
"""

import pytest
from datetime import datetime

from src.domain.entities.game import Game, Player
from src.domain.events import CardPlacedEvent, GameCompletedEvent, RoundStartedEvent
from src.domain.exceptions import GameStateError, InvalidCardPlacementError
from src.domain.value_objects import Card, CardPosition, GameRules


class TestGame:
    """Test suite for Game aggregate root."""

    def create_test_players(self, count=2):
        """Helper to create test players."""
        players = []
        for i in range(count):
            players.append(Player(f"player{i+1}", f"Player{i+1}"))
        return players

    def test_game_initialization_valid(self):
        """Test valid game initialization."""
        players = self.create_test_players(2)
        rules = GameRules.standard_rules()
        
        game = Game("game1", players, rules)
        
        assert game.id == "game1"
        assert len(game.players) == 2
        assert game.current_round == 1
        assert not game.is_completed
        assert game.rules == rules
        
        # Check initial cards dealt
        for player in game.players:
            assert len(player.hand_cards) == 5

    def test_game_initialization_invalid_player_count(self):
        """Test game initialization with invalid player count."""
        # Too few players
        with pytest.raises(GameStateError, match="OFC games require 2-4 players"):
            Game("game1", [Player("p1", "Player1")], GameRules())
        
        # Too many players
        players = [Player(f"p{i}", f"Player{i}") for i in range(5)]
        with pytest.raises(GameStateError, match="OFC games require 2-4 players"):
            Game("game1", players, GameRules())

    def test_game_initialization_duplicate_player_ids(self):
        """Test game initialization with duplicate player IDs."""
        players = [
            Player("player1", "Alice"),
            Player("player1", "Bob"),  # Duplicate ID
        ]
        
        with pytest.raises(GameStateError, match="All players must have unique IDs"):
            Game("game1", players, GameRules())

    def test_get_current_player(self):
        """Test getting current player."""
        players = self.create_test_players(3)
        game = Game("game1", players, GameRules())
        
        current = game.get_current_player()
        assert current in players
        assert current.id == "player1"  # First player starts

    def test_get_current_player_completed_game(self):
        """Test getting current player from completed game."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        # Force completion
        game._completed_at = datetime.utcnow()
        
        with pytest.raises(GameStateError, match="Game is already completed"):
            game.get_current_player()

    def test_place_card_valid(self):
        """Test valid card placement."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        current_player = game.get_current_player()
        card = current_player.hand_cards[0]
        
        # Place card
        game.place_card(current_player.id, card, CardPosition.TOP)
        
        # Verify card was placed
        assert card in current_player.top_row
        assert card not in current_player.hand_cards
        
        # Check domain event
        events = game.get_domain_events()
        card_placed_events = [e for e in events if isinstance(e, CardPlacedEvent)]
        assert len(card_placed_events) >= 1
        last_event = card_placed_events[-1]
        assert last_event.player_id == current_player.id
        assert last_event.card == card
        assert last_event.position == CardPosition.TOP

    def test_place_card_wrong_turn(self):
        """Test placing card when it's not player's turn."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        # Try to place card for non-current player
        non_current = players[1]
        card = Card.from_string("As")
        
        with pytest.raises(GameStateError, match="not player"):
            game.place_card(non_current.id, card, CardPosition.TOP)

    def test_place_card_completed_game(self):
        """Test placing card in completed game."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        # Force completion
        game._completed_at = datetime.utcnow()
        
        with pytest.raises(GameStateError, match="Cannot place cards in completed game"):
            game.place_card("player1", Card.from_string("As"), CardPosition.TOP)

    def test_place_card_invalid_player(self):
        """Test placing card for non-existent player."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        with pytest.raises(GameStateError, match="not player"):
            game.place_card("invalid_id", Card.from_string("As"), CardPosition.TOP)

    def test_place_card_unavailable_card(self):
        """Test placing card that's not available."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        current_player = game.get_current_player()
        # Try to place a card that's not in deck or hand
        unavailable_card = Card.from_string("As")
        # Remove from deck if present
        game._deck._cards = [c for c in game._deck._cards if c != unavailable_card]
        
        with pytest.raises(InvalidCardPlacementError, match="Cannot place"):
            game.place_card(current_player.id, unavailable_card, CardPosition.TOP)

    def test_turn_advancement(self):
        """Test turn advancement after card placement."""
        players = self.create_test_players(3)
        game = Game("game1", players, GameRules())
        
        # Player 1's turn
        assert game.get_current_player().id == "player1"
        card1 = game.get_current_player().hand_cards[0]
        game.place_card("player1", card1, CardPosition.TOP)
        
        # Should advance to player 2
        assert game.get_current_player().id == "player2"
        card2 = game.get_current_player().hand_cards[0]
        game.place_card("player2", card2, CardPosition.MIDDLE)
        
        # Should advance to player 3
        assert game.get_current_player().id == "player3"

    def test_validate_layout(self):
        """Test layout validation."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        # Valid for incomplete layout
        assert game.validate_layout("player1")
        
        # Invalid player
        assert not game.validate_layout("invalid_player")

    def test_get_analysis_position(self):
        """Test creating position snapshot for analysis."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        position = game.get_analysis_position()
        
        assert position.game_id == "game1"
        assert len(position.players_hands) == 2
        assert position.current_player_id == game.get_current_player().id
        assert position.round_number == 1
        assert position.rules == game.rules

    def test_calculate_scores(self):
        """Test score calculation."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        scores = game.calculate_scores()
        
        assert len(scores) == 2
        assert "player1" in scores
        assert "player2" in scores
        # Placeholder implementation returns 0 scores
        assert scores["player1"].total_points == 0
        assert scores["player2"].total_points == 0

    def test_domain_events(self):
        """Test domain event generation."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        # Should have round started event
        events = game.get_domain_events()
        round_events = [e for e in events if isinstance(e, RoundStartedEvent)]
        assert len(round_events) >= 1
        assert round_events[0].round_number == 1
        
        # Clear events
        game.clear_domain_events()
        assert len(game.get_domain_events()) == 0

    def test_fantasy_land_rules_integration(self):
        """Test fantasy land rules are checked on game completion."""
        players = self.create_test_players(2)
        rules = GameRules(fantasy_land_enabled=True)
        game = Game("game1", players, rules)
        
        # This test mainly verifies the integration exists
        # Detailed fantasy land testing is in test_fantasy_land_manager.py
        
        # The game should check fantasy land on completion
        # We can't easily test the full flow without mocking,
        # but we can verify the structure is in place
        assert hasattr(game, "_check_fantasy_land_qualification")

    def test_game_representation(self):
        """Test string representation of game."""
        players = self.create_test_players(2)
        game = Game("game1", players, GameRules())
        
        repr_str = repr(game)
        assert "Game" in repr_str
        assert "game1" in repr_str
        assert "players=2" in repr_str
        assert "round 1" in repr_str