import time

import pytest

from ofc.card import Card
from ofc.layout import is_foul, total_royalty
from ofc.solver import best_fantasyland_layout


def cards(*strs: str) -> list[Card]:
    return [Card.from_str(s) for s in strs]


def test_rejects_too_few():
    with pytest.raises(ValueError, match="13-17 cards"):
        best_fantasyland_layout(cards("As", "Kh"))


def test_rejects_too_many():
    c = [Card.from_str(s) for s in
         ["As", "Ah", "Ad", "Ac", "Ks", "Kh", "Kd", "Kc",
          "Qs", "Qh", "Qd", "Qc", "Js", "Jh", "Jd", "Jc",
          "Ts", "Th"]]
    with pytest.raises(ValueError, match="13-17 cards"):
        best_fantasyland_layout(c)


def test_rejects_duplicates():
    c = cards("As", "As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c", "6s", "5h", "4d", "3c", "2s")
    with pytest.raises(ValueError, match="duplicate"):
        best_fantasyland_layout(c)


def test_n13_delegates_to_best_layout():
    c = cards("As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c", "6s", "5h", "4d", "3c", "2s")
    layout = best_fantasyland_layout(c)
    assert layout is not None
    assert not is_foul(layout)
    assert total_royalty(layout) == 6


def test_n14_discards_obvious_trash():
    # 13-card optimum is 32 (test_quads_and_full_house). Add 4d as trash.
    c = cards("As", "Ah", "Ad", "Ac", "Ks", "Kh", "Kd", "Qs", "Qh", "Qc", "Jh", "2c", "3d", "4d")
    layout = best_fantasyland_layout(c)
    assert layout is not None
    assert not is_foul(layout)
    # Same 32 — no better layout possible by including 4d
    assert total_royalty(layout) == 32


def test_n14_finds_royal_flush_with_extra_card():
    # Royal flush in hearts + setup, plus one extra
    c = cards("Th", "Jh", "Qh", "Kh", "Ah", "2c", "3d", "4s", "5h",
              "6c", "7h", "8d", "9s", "2d")
    layout = best_fantasyland_layout(c)
    assert layout is not None
    assert not is_foul(layout)
    # 13-card optimum was 29 (royal 25 + middle straight 4). Discarding 2d
    # should give same; with 2d, no improvement possible.
    assert total_royalty(layout) == 29


def test_n14_completes_in_reasonable_time():
    c = cards("As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c", "6s",
              "5h", "4d", "3c", "2s", "2c")
    start = time.perf_counter()
    layout = best_fantasyland_layout(c)
    elapsed = time.perf_counter() - start
    assert layout is not None
    # 14 calls to best_layout, ~3s on dev machine
    assert elapsed < 10.0, f"took {elapsed:.2f}s"
