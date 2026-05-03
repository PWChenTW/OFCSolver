import random

import pytest

from ofc.card import Card
from ofc.layout import Layout
from ofc.mc import mc_ev_against_unknown


def L(front, middle, back) -> Layout:
    return Layout.from_strs(front, middle, back)


def seen_of(layout: Layout) -> set[Card]:
    return set(layout.front + layout.middle + layout.back)


def test_mc_seed_reproducible():
    layout = L(
        ["As", "Ah", "2c"],
        ["5s", "5h", "5d", "7c", "8c"],
        ["9h", "9c", "9d", "Th", "Td"],
    )
    seen = seen_of(layout)
    ev1 = mc_ev_against_unknown(layout, seen, n_rollouts=100, rng=random.Random(42))
    ev2 = mc_ev_against_unknown(layout, seen, n_rollouts=100, rng=random.Random(42))
    assert ev1 == ev2


def test_mc_strong_layout_positive_ev():
    # Strong layout: AA front + trips 5 middle + full house back (royalty 17)
    layout = L(
        ["As", "Ah", "2c"],
        ["5s", "5h", "5d", "7c", "8c"],
        ["9h", "9c", "9d", "Th", "Td"],
    )
    ev = mc_ev_against_unknown(
        layout, seen_of(layout), n_rollouts=300, rng=random.Random(1)
    )
    assert ev > 0


def test_mc_stronger_layout_has_higher_ev():
    weak = L(
        ["3d", "4c", "5s"],
        ["6h", "7s", "8c", "9d", "Jc"],
        ["Qh", "Kc", "2h", "3h", "4h"],
    )
    strong = L(
        ["As", "Ah", "2c"],
        ["5s", "5h", "5d", "7c", "8c"],
        ["9h", "9c", "9d", "Th", "Td"],
    )
    ev_weak = mc_ev_against_unknown(
        weak, seen_of(weak), n_rollouts=300, rng=random.Random(1)
    )
    ev_strong = mc_ev_against_unknown(
        strong, seen_of(strong), n_rollouts=300, rng=random.Random(1)
    )
    assert ev_strong > ev_weak


def test_mc_increasing_rollouts_converges():
    # EV should stabilize as n_rollouts grows (sanity check, not strict)
    layout = L(
        ["As", "Ah", "2c"],
        ["5s", "5h", "5d", "7c", "8c"],
        ["9h", "9c", "9d", "Th", "Td"],
    )
    seen = seen_of(layout)
    rng_a = random.Random(7)
    rng_b = random.Random(7)
    ev_small = mc_ev_against_unknown(layout, seen, n_rollouts=50, rng=rng_a)
    ev_large = mc_ev_against_unknown(layout, seen, n_rollouts=500, rng=rng_b)
    # They share initial draws (same seed) but differ in count; loose bound
    assert abs(ev_small - ev_large) < 10  # both should be in ballpark for strong layout


def test_mc_rejects_when_too_many_seen():
    layout = L(
        ["As", "Ah", "2c"],
        ["5s", "5h", "5d", "7c", "8c"],
        ["9h", "9c", "9d", "Th", "Td"],
    )
    # Mark all 52 cards as seen
    from ofc.card import full_deck
    seen = set(full_deck())
    with pytest.raises(ValueError, match="available"):
        mc_ev_against_unknown(layout, seen, n_rollouts=10, rng=random.Random(0))
