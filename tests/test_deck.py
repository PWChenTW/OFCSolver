import pytest

from ofc.card import full_deck
from ofc.deck import Deck


def test_fresh_deck_has_52():
    assert Deck().remaining == 52


def test_deal_reduces_remaining():
    d = Deck(seed=0)
    d.deal(5)
    assert d.remaining == 47
    d.deal(3)
    assert d.remaining == 44


def test_deal_returns_unique_cards():
    d = Deck(seed=0)
    cards = d.deal(13)
    assert len(cards) == 13
    assert len(set(cards)) == 13


def test_deal_all_yields_full_deck():
    d = Deck(seed=42)
    all_cards = d.deal(52)
    assert len(all_cards) == 52
    assert set(all_cards) == set(full_deck())
    assert d.remaining == 0


def test_deal_too_many_raises():
    d = Deck()
    with pytest.raises(ValueError, match="cards left"):
        d.deal(53)


def test_deal_negative_raises():
    d = Deck()
    with pytest.raises(ValueError, match="negative"):
        d.deal(-1)


def test_seed_is_reproducible():
    a = Deck(seed=123).deal(52)
    b = Deck(seed=123).deal(52)
    assert a == b


def test_different_seed_gives_different_order():
    a = Deck(seed=1).deal(52)
    b = Deck(seed=2).deal(52)
    assert a != b


def test_streets_dont_overlap_two_players():
    # Pineapple deal sequence for 2 players: street 0 = 5+5, streets 1-4 = 3+3 each
    d = Deck(seed=7)
    s0_p1 = d.deal(5)
    s0_p2 = d.deal(5)
    streets = [(d.deal(3), d.deal(3)) for _ in range(4)]

    seen = set(s0_p1) | set(s0_p2)
    for p1, p2 in streets:
        assert not (set(p1) & seen)
        assert not (set(p2) & seen)
        seen |= set(p1) | set(p2)

    # 2*5 + 2*3*4 = 34 dealt, 18 remain
    assert d.remaining == 18
    assert len(seen) == 34
