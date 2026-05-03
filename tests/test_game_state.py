import pytest

from ofc.card import Card
from ofc.game_state import GameState, Move, apply_move, enumerate_moves


def cards(*strs: str) -> list[Card]:
    return [Card.from_str(s) for s in strs]


def test_initial_state():
    s = GameState()
    assert s.street == 0
    assert s.is_done is False
    assert s.front_capacity() == 3
    assert s.middle_capacity() == 5
    assert s.back_capacity() == 5
    assert s.slots_remaining() == 13
    assert s.cards_used() == set()


def test_apply_move_advances_street():
    s = GameState()
    h = cards("As", "Kh", "Qd", "Jc", "Ts")
    m = Move(front_adds=tuple(h[:1]), middle_adds=tuple(h[1:3]), back_adds=tuple(h[3:5]))
    s2 = apply_move(s, m)
    assert s2.street == 1
    assert s2.front == (h[0],)
    assert s2.middle == (h[1], h[2])
    assert s2.back == (h[3], h[4])
    assert s2.discards == ()


def test_apply_move_records_discard():
    s = GameState(street=1)
    a, b, d = cards("As", "Kh", "Qd")
    m = Move(front_adds=(), middle_adds=(a,), back_adds=(b,), discard=d)
    s2 = apply_move(s, m)
    assert s2.street == 2
    assert s2.discards == (d,)


def test_enum_street_0_count_from_empty():
    s = GameState()
    h = cards("As", "Kh", "Qd", "Jc", "Ts")
    moves = enumerate_moves(s, h)
    # 5 cards, 3 piles each, capacities (3, 5, 5). 3^5 = 243.
    # Exclude only those with > 3 cards in front.
    # # invalid = sum_{k=4}^{5} C(5,k) * 2^(5-k) = 5*2 + 1*1 = 11
    # valid = 243 - 11 = 232
    assert len(moves) == 232


def test_enum_street_1_count_after_full_first_street():
    # All 5 placed in middle and back (e.g., 0 in front, 2 mid, 3 back)
    h0 = cards("As", "Kh", "Qd", "Jc", "Ts")
    s = GameState(street=1, middle=(h0[0], h0[1]), back=(h0[2], h0[3], h0[4]))
    h1 = cards("9h", "8d", "7c")
    moves = enumerate_moves(s, h1)
    # 3 discard choices × 3^2 = 27 total raw
    # After capacity (fc=3, mc=3, bc=2): all 27 should still fit (placing only 2)
    assert len(moves) == 27


def test_enum_done_state_returns_empty():
    s = GameState(street=5)
    assert enumerate_moves(s, []) == []


def test_enum_wrong_hand_size_raises():
    s = GameState(street=0)
    with pytest.raises(ValueError, match="5 cards"):
        enumerate_moves(s, cards("As", "Kh"))
    s = GameState(street=1)
    with pytest.raises(ValueError, match="3 cards"):
        enumerate_moves(s, cards("As", "Kh"))


def test_capacity_blocks_invalid_placement():
    # Front already full (3); street 1 placing 2 cards — none can go to front
    h0 = cards("As", "Kh", "Qd", "Jc", "Ts")
    s = GameState(
        street=1,
        front=(h0[0], h0[1], h0[2]),  # full
        middle=(h0[3],),
        back=(h0[4],),
    )
    h1 = cards("9h", "8d", "7c")
    moves = enumerate_moves(s, h1)
    # 3 discard × 3^2 = 27, but any move with a card to front is invalid.
    # For each discard, valid placements: (M,M), (M,B), (B,M), (B,B) → 4
    # Total: 3 × 4 = 12
    assert len(moves) == 12
    for m in moves:
        assert m.front_adds == ()
