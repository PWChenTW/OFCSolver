import random
import time

from ofc.card import Card
from ofc.game_state import GameState, apply_move
from ofc.mc import mc_finish_ev, recommend_move


def cards(*strs: str) -> list[Card]:
    return [Card.from_str(s) for s in strs]


def test_recommend_returns_none_when_done():
    s = GameState(street=5)
    assert recommend_move(s, []) is None


def test_recommend_seed_reproducible():
    s = GameState()
    h = cards("As", "Ah", "Ks", "Kh", "2c")
    a = recommend_move(s, h, n_rollouts=30, rng=random.Random(0))
    b = recommend_move(s, h, n_rollouts=30, rng=random.Random(0))
    assert a is not None and b is not None
    assert a[0] == b[0]
    assert a[1] == b[1]


def test_recommend_street4_obvious_choice():
    # placed 11: front (Qs Qh), middle (5s 5h 5d 7c 8c), back (9h 9c 9d Th Td)
    # slots: front 1, middle 0, back 0
    # hand 3 cards, must place 1 in front + discard 2 (one as discard, one... wait)
    # actually streets 1-4 always discard 1 + place 2. but only 1 slot exists.
    # That's a foul case in real play but our enumerator should still produce moves
    # where 1 of 2 placement attempts goes to front, the other has nowhere to go.
    # In our setup let's give 2 slots: front 1 + back 1
    s = GameState(
        street=4,
        front=(Card.from_str("Qs"), Card.from_str("Qh")),
        middle=(
            Card.from_str("5s"), Card.from_str("5h"), Card.from_str("5d"),
            Card.from_str("7c"), Card.from_str("8c"),
        ),
        back=(
            Card.from_str("9h"), Card.from_str("9c"), Card.from_str("9d"),
            Card.from_str("Th"),
        ),
        discards=(),
    )
    # slots: front=1, middle=0, back=1
    # Hand: Td (would complete back full house 999TT for royalty 6),
    #   2c (best to front to give QQ2 → still pair Q for front royalty 7),
    #   3d (trash to discard)
    h = cards("Td", "2c", "3d")
    result = recommend_move(s, h, n_rollouts=100, rng=random.Random(42))
    assert result is not None
    move, ev = result
    # Td obviously belongs in back (completes 999TT full house, +6 royalty).
    # The remaining 2c vs 3d split is near-equivalent (both QQ with low kicker,
    # same +7 front royalty), so let MC pick either.
    assert Card.from_str("Td") in move.back_adds
    placed_in_front = move.front_adds
    discarded = move.discard
    assert {placed_in_front[0], discarded} == {Card.from_str("2c"), Card.from_str("3d")}


def test_recommend_runs_in_reasonable_time():
    # Street 1 is the heaviest reasonable case (heuristic completion is fast)
    h0 = cards("As", "Ah", "2c", "5h", "5d")
    s = apply_move(
        GameState(),
        # place AA front, 5 5 middle, 2 back (just an example legal placement)
        __import__("ofc.game_state", fromlist=["Move"]).Move(
            front_adds=(h0[0], h0[1]),
            middle_adds=(h0[3], h0[4]),
            back_adds=(h0[2],),
        ),
    )
    h1 = cards("9h", "8d", "7c")
    start = time.perf_counter()
    result = recommend_move(s, h1, n_rollouts=100, rng=random.Random(0))
    elapsed = time.perf_counter() - start
    assert result is not None
    assert elapsed < 5.0, f"recommend_move took {elapsed:.2f}s"


def test_mc_finish_ev_seed_reproducible():
    s = GameState()
    seen: set[Card] = set()
    a = mc_finish_ev(s, seen, n_rollouts=50, rng=random.Random(7))
    b = mc_finish_ev(s, seen, n_rollouts=50, rng=random.Random(7))
    assert a == b
