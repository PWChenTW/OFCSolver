from itertools import combinations

from .card import Card
from .hand_eval import HandRank, evaluate_3, evaluate_5
from .layout import Layout, back_royalty, front_royalty, middle_royalty


def best_layout(cards: list[Card]) -> Layout | None:
    """從給定的 13 張牌找出 royalty 最高且不犯規的擺法。

    若所有擺法皆犯規（罕見），回傳 None。
    """
    if len(cards) != 13:
        raise ValueError(f"best_layout expects 13 cards, got {len(cards)}")
    if len(set(cards)) != 13:
        raise ValueError("duplicate cards in input")

    # Cache keyed on the tuple itself: combinations(rest, 5) preserves
    # original card order, so the same 5-card subset is always seen as
    # the same tuple regardless of which `front` it appeared under.
    eval5_cache: dict[tuple[Card, ...], HandRank] = {}

    best: Layout | None = None
    best_royalty = -1

    for front in combinations(cards, 3):
        front_rank = evaluate_3(list(front))
        front_r = front_royalty(front_rank)
        front_set = set(front)
        rest = tuple(c for c in cards if c not in front_set)

        for middle in combinations(rest, 5):
            middle_rank = eval5_cache.get(middle)
            if middle_rank is None:
                middle_rank = evaluate_5(list(middle))
                eval5_cache[middle] = middle_rank
            if middle_rank < front_rank:
                continue  # foul: front > middle

            middle_set = set(middle)
            back = tuple(c for c in rest if c not in middle_set)
            back_rank = eval5_cache.get(back)
            if back_rank is None:
                back_rank = evaluate_5(list(back))
                eval5_cache[back] = back_rank
            if back_rank < middle_rank:
                continue  # foul: middle > back

            r = front_r + middle_royalty(middle_rank) + back_royalty(back_rank)
            if r > best_royalty:
                best_royalty = r
                best = Layout(front, middle, back)

    return best
