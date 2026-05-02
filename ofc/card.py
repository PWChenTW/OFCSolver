from dataclasses import dataclass
from enum import IntEnum

RANK_CHARS = "23456789TJQKA"
SUIT_CHARS = "shdc"


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Suit(IntEnum):
    SPADES = 0
    HEARTS = 1
    DIAMONDS = 2
    CLUBS = 3


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{RANK_CHARS[self.rank - 2]}{SUIT_CHARS[self.suit]}"

    def __repr__(self) -> str:
        return f"Card({self})"

    @classmethod
    def from_str(cls, s: str) -> "Card":
        if len(s) != 2:
            raise ValueError(f"invalid card string: {s!r}")
        rank = Rank(RANK_CHARS.index(s[0].upper()) + 2)
        suit = Suit(SUIT_CHARS.index(s[1].lower()))
        return cls(rank, suit)


def full_deck() -> list[Card]:
    return [Card(Rank(r), Suit(s)) for r in range(2, 15) for s in range(4)]
