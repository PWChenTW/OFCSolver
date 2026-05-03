import itertools
from dataclasses import dataclass

from .card import Card

# 街 0: 發 5 擺 5 棄 0；街 1-4: 發 3 擺 2 棄 1
DRAWS_PER_STREET: dict[int, int] = {0: 5, 1: 3, 2: 3, 3: 3, 4: 3}


@dataclass(frozen=True)
class Move:
    """一街的動作：在各墩放入若干張，可能再棄 1 張（街 0 不棄）。"""
    front_adds: tuple[Card, ...] = ()
    middle_adds: tuple[Card, ...] = ()
    back_adds: tuple[Card, ...] = ()
    discard: Card | None = None


@dataclass(frozen=True)
class GameState:
    """從『我』視角的進行中 OFC 局面（同時擺牌規則下，對手 layout 不可見）。"""
    front: tuple[Card, ...] = ()
    middle: tuple[Card, ...] = ()
    back: tuple[Card, ...] = ()
    discards: tuple[Card, ...] = ()
    street: int = 0  # 下一個要玩的街道；> 4 表示已結束

    @property
    def is_done(self) -> bool:
        return self.street > 4

    def front_capacity(self) -> int:
        return 3 - len(self.front)

    def middle_capacity(self) -> int:
        return 5 - len(self.middle)

    def back_capacity(self) -> int:
        return 5 - len(self.back)

    def slots_remaining(self) -> int:
        return self.front_capacity() + self.middle_capacity() + self.back_capacity()

    def cards_used(self) -> set[Card]:
        return set(self.front + self.middle + self.back + self.discards)


def apply_move(state: GameState, move: Move) -> GameState:
    discards = state.discards
    if move.discard is not None:
        discards = discards + (move.discard,)
    return GameState(
        front=state.front + move.front_adds,
        middle=state.middle + move.middle_adds,
        back=state.back + move.back_adds,
        discards=discards,
        street=state.street + 1,
    )


def enumerate_moves(state: GameState, hand: list[Card]) -> list[Move]:
    """列舉當前 state + hand 下所有合法 moves（容量限制下）。"""
    if state.is_done:
        return []
    expected = DRAWS_PER_STREET[state.street]
    if len(hand) != expected:
        raise ValueError(
            f"street {state.street} expects {expected} cards, got {len(hand)}"
        )

    if state.street == 0:
        return _enum_no_discard(state, hand)
    return _enum_with_discard(state, hand)


def _enum_no_discard(state: GameState, hand: list[Card]) -> list[Move]:
    fc, mc, bc = state.front_capacity(), state.middle_capacity(), state.back_capacity()
    moves: list[Move] = []
    for assigns in itertools.product("FMB", repeat=len(hand)):
        f = tuple(c for c, p in zip(hand, assigns) if p == "F")
        m = tuple(c for c, p in zip(hand, assigns) if p == "M")
        b = tuple(c for c, p in zip(hand, assigns) if p == "B")
        if len(f) > fc or len(m) > mc or len(b) > bc:
            continue
        moves.append(Move(front_adds=f, middle_adds=m, back_adds=b))
    return moves


def _enum_with_discard(state: GameState, hand: list[Card]) -> list[Move]:
    fc, mc, bc = state.front_capacity(), state.middle_capacity(), state.back_capacity()
    moves: list[Move] = []
    for d_idx in range(3):
        discard = hand[d_idx]
        kept = [hand[i] for i in range(3) if i != d_idx]
        for assigns in itertools.product("FMB", repeat=2):
            f = tuple(c for c, p in zip(kept, assigns) if p == "F")
            m = tuple(c for c, p in zip(kept, assigns) if p == "M")
            b = tuple(c for c, p in zip(kept, assigns) if p == "B")
            if len(f) > fc or len(m) > mc or len(b) > bc:
                continue
            moves.append(
                Move(front_adds=f, middle_adds=m, back_adds=b, discard=discard)
            )
    return moves
