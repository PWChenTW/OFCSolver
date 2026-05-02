from collections import Counter
from enum import IntEnum

from .card import Card, Rank


class HandType(IntEnum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


HandRank = tuple[HandType, tuple[int, ...]]


def _straight_high(unique_ranks_desc: list[int]) -> int | None:
    if len(unique_ranks_desc) != 5:
        return None
    if unique_ranks_desc[0] - unique_ranks_desc[4] == 4:
        return unique_ranks_desc[0]
    if unique_ranks_desc == [Rank.ACE, 5, 4, 3, 2]:
        return 5
    return None


def evaluate_5(cards: list[Card]) -> HandRank:
    if len(cards) != 5:
        raise ValueError(f"evaluate_5 expects 5 cards, got {len(cards)}")

    ranks_desc = sorted((c.rank for c in cards), reverse=True)
    suits = [c.suit for c in cards]
    counts = Counter(ranks_desc)

    is_flush = len(set(suits)) == 1
    unique_ranks_desc = sorted(counts.keys(), reverse=True)
    straight_high = _straight_high(unique_ranks_desc)

    if is_flush and straight_high is not None:
        if straight_high == Rank.ACE:
            return (HandType.ROYAL_FLUSH, (Rank.ACE,))
        return (HandType.STRAIGHT_FLUSH, (straight_high,))

    count_pattern = tuple(sorted(counts.values(), reverse=True))

    if count_pattern == (4, 1):
        four = max(r for r, c in counts.items() if c == 4)
        kicker = max(r for r, c in counts.items() if c == 1)
        return (HandType.FOUR_OF_A_KIND, (four, kicker))

    if count_pattern == (3, 2):
        three = max(r for r, c in counts.items() if c == 3)
        pair = max(r for r, c in counts.items() if c == 2)
        return (HandType.FULL_HOUSE, (three, pair))

    if is_flush:
        return (HandType.FLUSH, tuple(ranks_desc))

    if straight_high is not None:
        return (HandType.STRAIGHT, (straight_high,))

    if count_pattern == (3, 1, 1):
        three = max(r for r, c in counts.items() if c == 3)
        kickers = sorted((r for r, c in counts.items() if c == 1), reverse=True)
        return (HandType.THREE_OF_A_KIND, (three, *kickers))

    if count_pattern == (2, 2, 1):
        pairs = sorted((r for r, c in counts.items() if c == 2), reverse=True)
        kicker = max(r for r, c in counts.items() if c == 1)
        return (HandType.TWO_PAIR, (*pairs, kicker))

    if count_pattern == (2, 1, 1, 1):
        pair = max(r for r, c in counts.items() if c == 2)
        kickers = sorted((r for r, c in counts.items() if c == 1), reverse=True)
        return (HandType.PAIR, (pair, *kickers))

    return (HandType.HIGH_CARD, tuple(ranks_desc))


def evaluate_3(cards: list[Card]) -> HandRank:
    if len(cards) != 3:
        raise ValueError(f"evaluate_3 expects 3 cards, got {len(cards)}")

    ranks_desc = sorted((c.rank for c in cards), reverse=True)
    counts = Counter(ranks_desc)
    count_pattern = tuple(sorted(counts.values(), reverse=True))

    if count_pattern == (3,):
        return (HandType.THREE_OF_A_KIND, (ranks_desc[0],))

    if count_pattern == (2, 1):
        pair = max(r for r, c in counts.items() if c == 2)
        kicker = max(r for r, c in counts.items() if c == 1)
        return (HandType.PAIR, (pair, kicker))

    return (HandType.HIGH_CARD, tuple(ranks_desc))
