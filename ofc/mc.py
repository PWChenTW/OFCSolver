import random
from typing import Callable

from .card import Card, full_deck
from .layout import Layout
from .scoring import settle
from .solver import heuristic_layout

OpponentPolicy = Callable[[list[Card]], Layout]


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

    seen_cards 應包含所有「我已知不在對手手中」的牌：我自己的 13 張、
    我已棄的牌（私密）、若我能看到對手已放的牌也包含進去。
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
