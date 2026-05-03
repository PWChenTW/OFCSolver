import random
from typing import Callable

from .card import Card, full_deck
from .game_state import GameState, Move, apply_move, enumerate_moves
from .layout import Layout
from .scoring import settle
from .solver import heuristic_completion, heuristic_layout

OpponentPolicy = Callable[[list[Card]], Layout]
CompletionPolicy = Callable[[GameState, list[Card]], Layout]


def mc_ev_against_unknown(
    my_layout: Layout,
    seen_cards: set[Card],
    n_rollouts: int = 1000,
    opponent_policy: OpponentPolicy = heuristic_layout,
    rng: random.Random | None = None,
) -> float:
    """Monte Carlo: 估算 my_layout 對未知對手的 EV（從我方視角的淨分）。

    從 (full deck - seen_cards) 隨機抽 13 張當對手手牌，丟給 opponent_policy
    決定擺法，跑 N 次 rollout 平均 settle()。
    """
    if rng is None:
        rng = random.Random()

    available = [c for c in full_deck() if c not in seen_cards]
    if len(available) < 13:
        raise ValueError(
            f"only {len(available)} cards available, need 13 for opponent"
        )

    total = 0
    for _ in range(n_rollouts):
        opp_cards = rng.sample(available, 13)
        opp_layout = opponent_policy(opp_cards)
        total += settle(my_layout, opp_layout)
    return total / n_rollouts


def mc_finish_ev(
    state: GameState,
    seen_cards: set[Card],
    n_rollouts: int = 500,
    completion_policy: CompletionPolicy = heuristic_completion,
    opponent_policy: OpponentPolicy = heuristic_layout,
    rng: random.Random | None = None,
) -> float:
    """從 state 開始 rollout 到結局，估從我方視角的 EV。

    每次 rollout：抽 (slots_remaining + 13) 張 — 前段給我未來、後段給對手 13 張，
    把我方未來牌透過 completion_policy 補齊 layout，對手丟給 opponent_policy。
    這個近似把「我未來棄牌的決策」忽略，視同「未來會剛好抽到我會擺的那些牌」，
    EV 估計通常偏樂觀但 MVP 階段足以區分動作優劣。
    """
    if rng is None:
        rng = random.Random()

    slots = state.slots_remaining()
    available = [c for c in full_deck() if c not in seen_cards]
    if len(available) < slots + 13:
        raise ValueError(
            f"only {len(available)} cards available, need {slots + 13}"
        )

    total = 0
    for _ in range(n_rollouts):
        sample = rng.sample(available, slots + 13)
        my_future = sample[:slots]
        opp_cards = sample[slots:]
        my_layout = completion_policy(state, my_future)
        opp_layout = opponent_policy(opp_cards)
        total += settle(my_layout, opp_layout)
    return total / n_rollouts


def recommend_move(
    state: GameState,
    hand: list[Card],
    n_rollouts: int = 500,
    rng: random.Random | None = None,
) -> tuple[Move, float] | None:
    """列舉合法 moves，對每個 move 跑 MC rollout，回傳 (最佳 move, EV)。

    若無合法 moves（state 已結束）回傳 None。
    為公平比較，每個 move 用相同 seed 起頭的 RNG 跑 rollout。
    """
    moves = enumerate_moves(state, hand)
    if not moves:
        return None

    base_seed = rng.random() if rng is not None else None
    seen = state.cards_used() | set(hand)

    best_move: Move | None = None
    best_ev = float("-inf")
    for m in moves:
        rng_for_move = (
            random.Random(base_seed) if base_seed is not None else random.Random()
        )
        ns = apply_move(state, m)
        ev = mc_finish_ev(ns, seen, n_rollouts=n_rollouts, rng=rng_for_move)
        if ev > best_ev:
            best_ev = ev
            best_move = m

    assert best_move is not None
    return best_move, best_ev
