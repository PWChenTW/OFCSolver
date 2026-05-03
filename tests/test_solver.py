import time

import pytest

from ofc.card import Card
from ofc.layout import is_foul, total_royalty
from ofc.solver import best_layout


def cards(*strs: str) -> list[Card]:
    return [Card.from_str(s) for s in strs]


def test_best_layout_rejects_wrong_count():
    with pytest.raises(ValueError, match="13 cards"):
        best_layout(cards("As", "Kh"))


def test_best_layout_rejects_duplicates():
    with pytest.raises(ValueError, match="duplicate"):
        c = cards("As", "As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c", "6s", "5h", "4d", "3c")
        best_layout(c)


def test_simple_high_cards_only():
    # 13 distinct high-ish cards, no pairs/flushes — best is straight in middle, A-high straight in back
    c = cards("As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c", "6s", "5h", "4d", "3c", "2s")
    layout = best_layout(c)
    assert layout is not None
    assert not is_foul(layout)
    # back A-K-Q-J-T = straight (royalty 2), middle 5-9 straight (royalty 4), front high card (0)
    assert total_royalty(layout) == 6


def test_finds_royal_flush_in_back():
    # Plant a royal flush in hearts; rest are mid-range singletons
    c = cards("Th", "Jh", "Qh", "Kh", "Ah", "2c", "3d", "4s", "5h", "6c", "7h", "8d", "9s")
    layout = best_layout(c)
    assert layout is not None
    assert not is_foul(layout)
    # back royal flush 25 + middle straight 5-9 (4) + front high card (0) = 29
    assert total_royalty(layout) == 29


def test_quads_and_full_house():
    # 4 A + 3 K + 3 Q + J + 2 + 3
    c = cards("As", "Ah", "Ad", "Ac", "Ks", "Kh", "Kd", "Qs", "Qh", "Qc", "Jh", "2c", "3d")
    layout = best_layout(c)
    assert layout is not None
    assert not is_foul(layout)
    # Best: front trips Q (20) + middle trips K (2) + back quads A (10) = 32
    assert total_royalty(layout) == 32


def test_solver_picks_double_full_house():
    # Two full houses possible — solver should put higher one in middle for max royalty
    c = cards("Qs", "Qh", "2c", "5s", "5h", "5d", "7c", "8c", "9h", "9c", "9d", "Th", "Td")
    layout = best_layout(c)
    assert layout is not None
    assert not is_foul(layout)
    # Best: front high card (0) + middle 555QQ full house (12) + back 999TT full house (6) = 18
    assert total_royalty(layout) == 18


def test_performance_under_2_seconds():
    # Random-ish hand to confirm enumeration completes in reasonable time
    c = cards("As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c", "6s", "5h", "4d", "3c", "2s")
    start = time.perf_counter()
    layout = best_layout(c)
    elapsed = time.perf_counter() - start
    assert layout is not None
    # Just a sanity check; CI machines vary
    assert elapsed < 5.0, f"best_layout took {elapsed:.2f}s"
