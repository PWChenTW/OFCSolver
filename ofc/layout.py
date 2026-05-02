from dataclasses import dataclass

from .card import Card
from .hand_eval import HandRank, HandType, evaluate_3, evaluate_5

MIDDLE_ROYALTY: dict[HandType, int] = {
    HandType.THREE_OF_A_KIND: 2,
    HandType.STRAIGHT: 4,
    HandType.FLUSH: 8,
    HandType.FULL_HOUSE: 12,
    HandType.FOUR_OF_A_KIND: 20,
    HandType.STRAIGHT_FLUSH: 30,
    HandType.ROYAL_FLUSH: 50,
}

BACK_ROYALTY: dict[HandType, int] = {
    HandType.STRAIGHT: 2,
    HandType.FLUSH: 4,
    HandType.FULL_HOUSE: 6,
    HandType.FOUR_OF_A_KIND: 10,
    HandType.STRAIGHT_FLUSH: 15,
    HandType.ROYAL_FLUSH: 25,
}


@dataclass(frozen=True)
class Layout:
    front: tuple[Card, ...]
    middle: tuple[Card, ...]
    back: tuple[Card, ...]

    def __post_init__(self) -> None:
        if len(self.front) != 3:
            raise ValueError(f"front needs 3 cards, got {len(self.front)}")
        if len(self.middle) != 5:
            raise ValueError(f"middle needs 5 cards, got {len(self.middle)}")
        if len(self.back) != 5:
            raise ValueError(f"back needs 5 cards, got {len(self.back)}")
        all_cards = self.front + self.middle + self.back
        if len(set(all_cards)) != 13:
            raise ValueError("duplicate cards in layout")

    @classmethod
    def from_strs(
        cls, front: list[str], middle: list[str], back: list[str]
    ) -> "Layout":
        return cls(
            tuple(Card.from_str(s) for s in front),
            tuple(Card.from_str(s) for s in middle),
            tuple(Card.from_str(s) for s in back),
        )

    def front_rank(self) -> HandRank:
        return evaluate_3(list(self.front))

    def middle_rank(self) -> HandRank:
        return evaluate_5(list(self.middle))

    def back_rank(self) -> HandRank:
        return evaluate_5(list(self.back))


def is_foul(layout: Layout) -> bool:
    front = layout.front_rank()
    middle = layout.middle_rank()
    back = layout.back_rank()
    return front > middle or middle > back


def front_royalty(rank: HandRank) -> int:
    hand_type, tiebreak = rank
    if hand_type == HandType.PAIR:
        pair_rank = tiebreak[0]
        if pair_rank >= 6:
            return pair_rank - 5
        return 0
    if hand_type == HandType.THREE_OF_A_KIND:
        return tiebreak[0] + 8
    return 0


def middle_royalty(rank: HandRank) -> int:
    return MIDDLE_ROYALTY.get(rank[0], 0)


def back_royalty(rank: HandRank) -> int:
    return BACK_ROYALTY.get(rank[0], 0)


def total_royalty(layout: Layout) -> int:
    if is_foul(layout):
        return 0
    return (
        front_royalty(layout.front_rank())
        + middle_royalty(layout.middle_rank())
        + back_royalty(layout.back_rank())
    )
