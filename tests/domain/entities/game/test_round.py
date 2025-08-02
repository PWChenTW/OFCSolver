"""
Tests for Round Entity
"""

import pytest
from datetime import datetime

from src.domain.entities.game.round import Round, RoundStatus, CardPlacement
from src.domain.value_objects import Card, CardPosition


class TestRound:
    """Test suite for Round entity."""

    def test_round_initialization(self):
        """Test round creation and initial state."""
        player_ids = ["player1", "player2", "player3"]
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=player_ids,
            starting_player_id="player2",
        )

        assert round_entity.id == "round1"
        assert round_entity.round_number == 1
        assert round_entity.game_id == "game1"
        assert round_entity.status == RoundStatus.ACTIVE
        assert round_entity.player_ids == player_ids
        assert round_entity.starting_player_id == "player2"
        assert round_entity.is_active
        assert not round_entity.is_completed
        assert isinstance(round_entity.started_at, datetime)
        assert round_entity.completed_at is None
        assert len(round_entity.placements) == 0

    def test_get_current_player(self):
        """Test getting current player in round."""
        player_ids = ["player1", "player2", "player3"]
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=player_ids,
            starting_player_id="player2",
        )

        # Should start with player2
        assert round_entity.get_current_player_id() == "player2"

    def test_get_current_player_inactive_round(self):
        """Test getting current player from inactive round."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        # Complete the round
        round_entity._status = RoundStatus.COMPLETED

        assert round_entity.get_current_player_id() is None

    def test_has_player_acted(self):
        """Test checking if player has acted."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        assert not round_entity.has_player_acted("p1")
        assert not round_entity.has_player_acted("p2")

    def test_get_players_remaining(self):
        """Test getting players who haven't acted."""
        player_ids = ["p1", "p2", "p3"]
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=player_ids,
            starting_player_id="p1",
        )

        remaining = round_entity.get_players_remaining()
        assert len(remaining) == 3
        assert all(pid in remaining for pid in player_ids)

    def test_record_placement_valid(self):
        """Test recording valid card placement."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        card = Card.from_string("As")
        round_entity.record_placement("p1", card, CardPosition.TOP)

        # Check placement recorded
        assert round_entity.get_placement_count() == 1
        assert round_entity.has_player_acted("p1")
        assert not round_entity.has_player_acted("p2")

        # Check placement details
        placements = round_entity.placements
        assert len(placements) == 1
        assert placements[0].player_id == "p1"
        assert placements[0].card == card
        assert placements[0].position == CardPosition.TOP
        assert placements[0].sequence_number == 1

    def test_record_placement_wrong_turn(self):
        """Test recording placement when it's not player's turn."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        # Try to place for p2 when it's p1's turn
        with pytest.raises(ValueError, match="not player p2's turn"):
            round_entity.record_placement(
                "p2", Card.from_string("As"), CardPosition.TOP
            )

    def test_record_placement_inactive_round(self):
        """Test recording placement in inactive round."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        round_entity._status = RoundStatus.COMPLETED

        with pytest.raises(
            ValueError, match="Cannot record placement in inactive round"
        ):
            round_entity.record_placement(
                "p1", Card.from_string("As"), CardPosition.TOP
            )

    def test_record_placement_already_acted(self):
        """Test recording placement when player already acted."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        # First placement
        round_entity.record_placement("p1", Card.from_string("As"), CardPosition.TOP)

        # Try to place again for p1 (but it's now p2's turn)
        with pytest.raises(ValueError, match="not player p1's turn"):
            round_entity.record_placement(
                "p1", Card.from_string("Ks"), CardPosition.MIDDLE
            )

    def test_turn_advancement(self):
        """Test turn advancing after placement."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2", "p3"],
            starting_player_id="p1",
        )

        # p1's turn
        assert round_entity.get_current_player_id() == "p1"
        round_entity.record_placement("p1", Card.from_string("As"), CardPosition.TOP)

        # Should advance to p2
        assert round_entity.get_current_player_id() == "p2"
        round_entity.record_placement("p2", Card.from_string("Ks"), CardPosition.MIDDLE)

        # Should advance to p3
        assert round_entity.get_current_player_id() == "p3"

    def test_round_completion(self):
        """Test round completion when all players have acted."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        # Both players place cards
        round_entity.record_placement("p1", Card.from_string("As"), CardPosition.TOP)
        assert round_entity.is_active

        round_entity.record_placement("p2", Card.from_string("Ks"), CardPosition.MIDDLE)

        # Round should be completed
        assert round_entity.is_completed
        assert not round_entity.is_active
        assert round_entity.status == RoundStatus.COMPLETED
        assert round_entity.completed_at is not None

    def test_cancel_round(self):
        """Test cancelling a round."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        round_entity.cancel_round("Player disconnected")

        assert round_entity.status == RoundStatus.CANCELLED
        assert not round_entity.is_active
        assert round_entity.completed_at is not None

    def test_cancel_inactive_round(self):
        """Test cancelling an already inactive round."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        round_entity._status = RoundStatus.COMPLETED

        with pytest.raises(ValueError, match="Cannot cancel inactive round"):
            round_entity.cancel_round()

    def test_get_placements_by_player(self):
        """Test getting placements by specific player."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2", "p3"],
            starting_player_id="p1",
        )

        # Record placements
        round_entity.record_placement("p1", Card.from_string("As"), CardPosition.TOP)
        round_entity.record_placement("p2", Card.from_string("Ks"), CardPosition.MIDDLE)
        round_entity.record_placement("p3", Card.from_string("Qs"), CardPosition.BOTTOM)

        # Get p1's placements
        p1_placements = round_entity.get_placements_by_player("p1")
        assert len(p1_placements) == 1
        assert p1_placements[0].card == Card.from_string("As")

        # Get p2's placements
        p2_placements = round_entity.get_placements_by_player("p2")
        assert len(p2_placements) == 1
        assert p2_placements[0].card == Card.from_string("Ks")

    def test_get_turn_order(self):
        """Test getting turn order for round."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2", "p3"],
            starting_player_id="p2",
        )

        turn_order = round_entity.get_turn_order()
        # Should start with p2, then p3, then p1
        assert turn_order == ["p2", "p3", "p1"]

    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        elapsed = round_entity.get_elapsed_time()
        assert isinstance(elapsed, float)
        assert elapsed >= 0

    def test_get_round_summary(self):
        """Test getting round summary."""
        round_entity = Round(
            round_id="round1",
            round_number=1,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        # Add a placement
        round_entity.record_placement("p1", Card.from_string("As"), CardPosition.TOP)

        summary = round_entity.get_round_summary()

        assert isinstance(summary, dict)
        assert summary["round_id"] == "round1"
        assert summary["round_number"] == 1
        assert summary["game_id"] == "game1"
        assert summary["status"] == "active"
        assert summary["total_placements"] == 1
        assert summary["players_acted"] == 1
        assert summary["players_remaining"] == 1
        assert len(summary["placements"]) == 1

    def test_round_representation(self):
        """Test string representation of round."""
        round_entity = Round(
            round_id="round1",
            round_number=5,
            game_id="game1",
            player_ids=["p1", "p2"],
            starting_player_id="p1",
        )

        repr_str = repr(round_entity)
        assert "Round" in repr_str
        assert "round1" in repr_str
        assert "number=5" in repr_str
        assert "game1" in repr_str
        assert "placements=0/2" in repr_str
