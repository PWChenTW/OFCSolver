import pytest

from ofc.card import Card
from ofc.solver import heuristic_layout


def cards(*strs: str) -> list[Card]:
    return [Card.from_str(s) for s in strs]


def test_heuristic_returns_all_13_cards():
    c = cards("As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c", "6s", "5h", "4d", "3c", "2s")
    layout = heuristic_layout(c)
    assert set(layout.front + layout.middle + layout.back) == set(c)


def test_heuristic_pile_sizes():
    c = cards("As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c", "6s", "5h", "4d", "3c", "2s")
    layout = heuristic_layout(c)
    assert len(layout.front) == 3
    assert len(layout.middle) == 5
    assert len(layout.back) == 5


def test_heuristic_rejects_wrong_count():
    with pytest.raises(ValueError, match="13 cards"):
        heuristic_layout(cards("As", "Kh"))


def test_heuristic_back_has_strongest_high_card():
    # With distinct ranks, sort-by-rank means back contains 5 highest cards
    c = cards("As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c", "6s", "5h", "4d", "3c", "2s")
    layout = heuristic_layout(c)
    # back should contain A K Q J T (top 5)
    back_ranks = sorted(c.rank for c in layout.back)
    assert back_ranks == [10, 11, 12, 13, 14]
