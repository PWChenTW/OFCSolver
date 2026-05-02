import random

from .card import Card, full_deck


class Deck:
    def __init__(self, seed: int | None = None) -> None:
        self._cards: list[Card] = full_deck()
        random.Random(seed).shuffle(self._cards)

    def deal(self, n: int) -> list[Card]:
        if n < 0:
            raise ValueError(f"cannot deal negative count: {n}")
        if n > len(self._cards):
            raise ValueError(
                f"deck has {len(self._cards)} cards left, cannot deal {n}"
            )
        return [self._cards.pop() for _ in range(n)]

    @property
    def remaining(self) -> int:
        return len(self._cards)
