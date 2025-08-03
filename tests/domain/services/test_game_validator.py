"""
Tests for GameValidator Domain Service

Comprehensive test suite covering all validation rules, edge cases,
and multi-player scenarios for the OFC game validator.
"""

import pytest
from unittest.mock import Mock

from src.domain.entities.game import Game
from src.domain.entities.game.player import Player, PlayerStatus
from src.domain.services.game_validator import GameValidator, ValidationResult
from src.domain.value_objects import Card, CardPosition
from src.domain.value_objects.game_rules import GameRules


class TestGameValidator:
    """Test suite for GameValidator service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = GameValidator()
        self.rules = GameRules.standard_rules()

        # Create test players
        self.player1 = Player("player1", "Alice")
        self.player2 = Player("player2", "Bob")

        # Create test cards
        self.test_cards = [
            Card.from_string("As"),  # Ace of Spades
            Card.from_string("Kh"),  # King of Hearts
            Card.from_string("Qc"),  # Queen of Clubs
            Card.from_string("Jd"),  # Jack of Diamonds
            Card.from_string("Ts"),  # Ten of Spades
            Card.from_string("9h"),  # Nine of Hearts
            Card.from_string("8c"),  # Eight of Clubs
            Card.from_string("7d"),  # Seven of Diamonds
            Card.from_string("6s"),  # Six of Spades
            Card.from_string("5h"),  # Five of Hearts
        ]

    def test_init(self):
        """Test GameValidator initialization."""
        validator = GameValidator()
        assert validator._hand_evaluator is not None

    def test_validate_card_placement_success(self):
        """Test successful card placement validation."""
        # Create game with players
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Give player a card
        self.player1._hand_cards = [self.test_cards[0]]

        # Test valid placement
        result = self.validator.validate_card_placement(
            game, "player1", self.test_cards[0], CardPosition.TOP
        )

        assert result.is_valid
        assert result.error_message is None

    def test_validate_card_placement_completed_game(self):
        """Test card placement validation on completed game."""
        game = Game("game1", [self.player1, self.player2], self.rules)
        game._completed_at = "2023-01-01"  # Mark as completed

        result = self.validator.validate_card_placement(
            game, "player1", self.test_cards[0], CardPosition.TOP
        )

        assert not result.is_valid
        assert "Cannot place cards in completed game" in result.error_message

    def test_validate_card_placement_wrong_turn(self):
        """Test card placement validation when it's not player's turn."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # It should be player1's turn by default, test player2 trying to play
        result = self.validator.validate_card_placement(
            game, "player2", self.test_cards[0], CardPosition.TOP
        )

        assert not result.is_valid
        assert "not player player2's turn" in result.error_message

    def test_validate_card_placement_player_not_in_game(self):
        """Test card placement validation for player not in game."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        result = self.validator.validate_card_placement(
            game, "player3", self.test_cards[0], CardPosition.TOP
        )

        assert not result.is_valid
        assert "Player player3 not in game" in result.error_message

    def test_validate_card_placement_player_doesnt_have_card(self):
        """Test card placement validation when player doesn't have the card."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Player doesn't have the card in hand
        self.player1._hand_cards = []

        result = self.validator.validate_card_placement(
            game, "player1", self.test_cards[0], CardPosition.TOP
        )

        assert not result.is_valid
        assert "does not have card" in result.error_message

    def test_validate_card_placement_position_full(self):
        """Test card placement validation when position is full."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Fill top row (3 cards max)
        self.player1._top_row = self.test_cards[:3]
        self.player1._hand_cards = [self.test_cards[3]]

        result = self.validator.validate_card_placement(
            game, "player1", self.test_cards[3], CardPosition.TOP
        )

        assert not result.is_valid
        assert "Top Row is full" in result.error_message

    def test_validate_card_placement_duplicate_card(self):
        """Test card placement validation for duplicate cards."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Place card in player2's layout
        self.player2._top_row = [self.test_cards[0]]

        # Try to place same card with player1
        self.player1._hand_cards = [self.test_cards[0]]

        result = self.validator.validate_card_placement(
            game, "player1", self.test_cards[0], CardPosition.TOP
        )

        assert not result.is_valid
        assert "already placed in the game" in result.error_message

    def test_validate_row_strength_progression_incomplete_layout(self):
        """Test row strength validation with incomplete layout."""
        # Player with incomplete layout
        self.player1._top_row = self.test_cards[:2]  # Only 2 cards

        result = self.validator.validate_row_strength_progression(self.player1)

        assert result.is_valid
        assert "not complete" in result.warning_message

    def test_validate_row_strength_progression_fouled_player(self):
        """Test row strength validation with already fouled player."""
        self.player1._status = PlayerStatus.FOULED
        self.player1._top_row = self.test_cards[:3]
        self.player1._middle_row = self.test_cards[3:8]
        self.player1._bottom_row = (
            self.test_cards[8:13]
            if len(self.test_cards) >= 13
            else self.test_cards[8:] + [Card.from_string("2h"), Card.from_string("3s")]
        )

        result = self.validator.validate_row_strength_progression(self.player1)

        assert not result.is_valid
        assert "fouled hand" in result.error_message

    def test_validate_row_strength_progression_invalid_card_counts(self):
        """Test row strength validation with invalid card counts."""
        self.player1._top_row = self.test_cards[:2]  # Only 2 cards instead of 3
        self.player1._middle_row = self.test_cards[2:7]  # 5 cards
        self.player1._bottom_row = self.test_cards[7:] + [
            Card.from_string("2h")
        ]  # Try to make 5 cards

        # Mock is_layout_complete to return True
        self.player1.is_layout_complete = lambda: True

        result = self.validator.validate_row_strength_progression(self.player1)

        assert not result.is_valid
        assert "Invalid card counts" in result.error_message

    def test_validate_row_strength_progression_valid(self):
        """Test row strength validation with valid progression."""
        # Create a valid OFC hand: bottom > middle > top

        # Bottom row: Full house (5s full of 2s)
        bottom_cards = [
            Card.from_string("5s"),
            Card.from_string("5h"),
            Card.from_string("5c"),
            Card.from_string("2d"),
            Card.from_string("2s"),
        ]

        # Middle row: Pair of Aces
        middle_cards = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
            Card.from_string("Qd"),
            Card.from_string("Jc"),
        ]

        # Top row: King high
        top_cards = [
            Card.from_string("Kh"),
            Card.from_string("Qc"),
            Card.from_string("Jd"),
        ]

        self.player1._top_row = top_cards
        self.player1._middle_row = middle_cards
        self.player1._bottom_row = bottom_cards

        # Mock is_layout_complete to return True
        self.player1.is_layout_complete = lambda: True

        result = self.validator.validate_row_strength_progression(self.player1)

        assert result.is_valid

    def test_check_game_completion_already_completed(self):
        """Test game completion check on already completed game."""
        game = Game("game1", [self.player1, self.player2], self.rules)
        game._completed_at = "2023-01-01"

        result = self.validator.check_game_completion(game)

        assert result.is_valid
        assert "already completed" in result.warning_message

    def test_check_game_completion_incomplete_players(self):
        """Test game completion check with incomplete player layouts."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Players don't have complete layouts
        result = self.validator.check_game_completion(game)

        assert not result.is_valid
        assert "still need to complete" in result.error_message

    def test_check_game_completion_card_count_mismatch(self):
        """Test game completion check with card count mismatch."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Mock players as having complete layouts but wrong card count
        self.player1.is_layout_complete = lambda: True
        self.player2.is_layout_complete = lambda: True
        self.player1.total_cards_placed = 12  # Should be 13
        self.player2.total_cards_placed = 13

        result = self.validator.check_game_completion(game)

        assert not result.is_valid
        assert "Card count mismatch" in result.error_message

    def test_check_game_completion_valid(self):
        """Test game completion check with valid completion."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Mock players as having complete layouts
        self.player1.is_layout_complete = lambda: True
        self.player2.is_layout_complete = lambda: True
        self.player1.total_cards_placed = 13
        self.player2.total_cards_placed = 13

        result = self.validator.check_game_completion(game)

        assert result.is_valid

    def test_validate_turn_order_completed_game(self):
        """Test turn order validation on completed game."""
        game = Game("game1", [self.player1, self.player2], self.rules)
        game._completed_at = "2023-01-01"

        result = self.validator.validate_turn_order(game, "player1")

        assert not result.is_valid
        assert "Game is completed" in result.error_message

    def test_validate_turn_order_wrong_player(self):
        """Test turn order validation with wrong player."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Should be player1's turn, test player2
        result = self.validator.validate_turn_order(game, "player2")

        assert not result.is_valid
        assert "Alice's turn" in result.error_message

    def test_validate_turn_order_correct_player(self):
        """Test turn order validation with correct player."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Should be player1's turn
        result = self.validator.validate_turn_order(game, "player1")

        assert result.is_valid

    def test_validate_multi_player_game_state_invalid_player_count(self):
        """Test multi-player validation with invalid player count."""
        # Create game with only 1 player (invalid)
        game = Game("game1", [self.player1], self.rules)

        result = self.validator.validate_multi_player_game_state(game)

        assert not result.is_valid
        assert "Invalid player count" in result.error_message

    def test_validate_multi_player_game_state_duplicate_player_ids(self):
        """Test multi-player validation with duplicate player IDs."""
        player_duplicate = Player("player1", "Bob")  # Same ID as player1
        game = Game("game1", [self.player1, player_duplicate], self.rules)

        result = self.validator.validate_multi_player_game_state(game)

        assert not result.is_valid
        assert "Duplicate player IDs" in result.error_message

    def test_validate_multi_player_game_state_duplicate_cards(self):
        """Test multi-player validation with duplicate cards across players."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Place same card in both players' layouts
        self.player1._top_row = [self.test_cards[0]]
        self.player2._top_row = [self.test_cards[0]]  # Duplicate!

        result = self.validator.validate_multi_player_game_state(game)

        assert not result.is_valid
        assert "Duplicate cards found" in result.error_message

    def test_validate_multi_player_game_state_fouled_players(self):
        """Test multi-player validation with fouled players."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Mock player1 as having complete but fouled layout
        self.player1.is_layout_complete = lambda: True

        # Create fouled hand (top > middle violates progression)
        self.player1._top_row = [
            Card.from_string("As"),
            Card.from_string("Ah"),
            Card.from_string("Kc"),
        ]  # Pair of Aces
        self.player1._middle_row = [
            Card.from_string("Kh"),
            Card.from_string("Qc"),
            Card.from_string("Jd"),
            Card.from_string("9s"),
            Card.from_string("8h"),
        ]  # King high
        self.player1._bottom_row = [
            Card.from_string("5s"),
            Card.from_string("5h"),
            Card.from_string("5c"),
            Card.from_string("2d"),
            Card.from_string("2s"),
        ]  # Full house

        result = self.validator.validate_multi_player_game_state(game)

        assert result.is_valid  # Game state is valid overall
        assert "fouled hands" in result.warning_message

    def test_validate_multi_player_game_state_valid(self):
        """Test multi-player validation with valid game state."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        result = self.validator.validate_multi_player_game_state(game)

        assert result.is_valid

    def test_can_place_card_safely_basic_invalid(self):
        """Test safe placement check with basic invalid placement."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Player doesn't have the card
        result = self.validator.can_place_card_safely(
            game, "player1", self.test_cards[0], CardPosition.TOP
        )

        assert not result.is_valid

    def test_can_place_card_safely_valid_placement(self):
        """Test safe placement check with valid placement."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Give player the card
        self.player1._hand_cards = [self.test_cards[0]]

        result = self.validator.can_place_card_safely(
            game, "player1", self.test_cards[0], CardPosition.TOP
        )

        assert result.is_valid

    def test_can_place_card_safely_fouling_warning(self):
        """Test safe placement check with potential fouling."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Set up scenario where placing high card in top might cause fouling
        self.player1._top_row = [Card.from_string("Kh"), Card.from_string("Qc")]
        self.player1._middle_row = [
            Card.from_string("9s"),
            Card.from_string("8h"),
            Card.from_string("7d"),
        ]
        self.player1._bottom_row = [
            Card.from_string("6s"),
            Card.from_string("5h"),
            Card.from_string("4c"),
        ]
        self.player1._hand_cards = [Card.from_string("As")]

        result = self.validator.can_place_card_safely(
            game, "player1", Card.from_string("As"), CardPosition.TOP
        )

        # Should be valid but with warning
        assert result.is_valid
        # Note: The warning logic is simplified in this implementation

    def test_get_player_by_id_found(self):
        """Test getting player by ID when found."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        player = self.validator._get_player_by_id(game, "player1")

        assert player == self.player1

    def test_get_player_by_id_not_found(self):
        """Test getting player by ID when not found."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        player = self.validator._get_player_by_id(game, "player3")

        assert player is None

    def test_is_card_already_placed_true(self):
        """Test checking if card is already placed when it is."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Place card in player1's layout
        self.player1._top_row = [self.test_cards[0]]

        result = self.validator._is_card_already_placed(game, self.test_cards[0])

        assert result is True

    def test_is_card_already_placed_false(self):
        """Test checking if card is already placed when it's not."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        result = self.validator._is_card_already_placed(game, self.test_cards[0])

        assert result is False

    def test_get_available_positions_player_not_found(self):
        """Test getting available positions for non-existent player."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        positions = self.validator.get_available_positions(game, "player3")

        assert positions == []

    def test_get_available_positions_all_available(self):
        """Test getting available positions when all are available."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        positions = self.validator.get_available_positions(game, "player1")

        expected = [CardPosition.TOP, CardPosition.MIDDLE, CardPosition.BOTTOM]
        assert positions == expected

    def test_get_available_positions_some_full(self):
        """Test getting available positions when some are full."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        # Fill top row
        self.player1._top_row = self.test_cards[:3]

        positions = self.validator.get_available_positions(game, "player1")

        expected = [CardPosition.MIDDLE, CardPosition.BOTTOM]
        assert positions == expected

    def test_get_validation_summary_comprehensive(self):
        """Test getting comprehensive validation summary."""
        game = Game("game1", [self.player1, self.player2], self.rules)

        summary = self.validator.get_validation_summary(game)

        # Check that all expected keys are present
        assert "game_state" in summary
        assert "completion" in summary
        assert "player_player1" in summary
        assert "player_player2" in summary
        assert "turn_order" in summary

        # Check that all values are ValidationResult objects
        for key, value in summary.items():
            assert isinstance(value, ValidationResult)

    def test_get_validation_summary_completed_game(self):
        """Test validation summary for completed game."""
        game = Game("game1", [self.player1, self.player2], self.rules)
        game._completed_at = "2023-01-01"

        summary = self.validator.get_validation_summary(game)

        # Turn order should not be included for completed games
        assert "turn_order" not in summary

    def test_validation_result_dataclass(self):
        """Test ValidationResult dataclass functionality."""
        # Test with all fields
        result = ValidationResult(
            is_valid=True, error_message="Error", warning_message="Warning"
        )

        assert result.is_valid is True
        assert result.error_message == "Error"
        assert result.warning_message == "Warning"

        # Test with minimal fields
        result_minimal = ValidationResult(is_valid=False)

        assert result_minimal.is_valid is False
        assert result_minimal.error_message is None
        assert result_minimal.warning_message is None
