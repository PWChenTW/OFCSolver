from collections import Counter
from itertools import combinations

from .card import Card
from .hand_eval import HandRank, evaluate_3, evaluate_5
from .layout import (
    Layout,
    back_royalty,
    front_royalty,
    is_foul,
    middle_royalty,
    total_royalty,
)


def best_layout(
    cards: list[Card], _shared_eval5_cache: dict[tuple[Card, ...], HandRank] | None = None
) -> Layout | None:
    """從給定的 13 張牌找出 royalty 最高且不犯規的擺法。

    若所有擺法皆犯規（罕見），回傳 None。

    `_shared_eval5_cache` 是給 fantasyland 跨 call 共享 5-card 評估結果用的，
    一般使用者不需要傳。
    """
    if len(cards) != 13:
        raise ValueError(f"best_layout expects 13 cards, got {len(cards)}")
    if len(set(cards)) != 13:
        raise ValueError("duplicate cards in input")

    # Cache keyed on the tuple itself: combinations preserves the input
    # order, so the same 5-card subset is always seen as the same tuple
    # regardless of which `front` (or which fantasyland 13-subset) it
    # appeared under, as long as the original card order is consistent.
    eval5_cache: dict[tuple[Card, ...], HandRank] = (
        _shared_eval5_cache if _shared_eval5_cache is not None else {}
    )

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


def best_fantasyland_layout(cards: list[Card]) -> Layout | None:
    """Fantasyland: 從 13-17 張牌中選 13 張擺成最佳 layout，剩餘棄掉。

    Naive 實作：對每種「保留 13 張」的選法跑 best_layout 取最佳。
    14 張 ~2-3s；17 張會幾分鐘，目前先這樣，需要時再優化。
    """
    n = len(cards)
    if not (13 <= n <= 17):
        raise ValueError(f"fantasyland needs 13-17 cards, got {n}")
    if len(set(cards)) != n:
        raise ValueError("duplicate cards in input")

    if n == 13:
        return best_layout(cards)

    shared_cache: dict[tuple[Card, ...], HandRank] = {}
    best: Layout | None = None
    best_royalty = -1

    for subset in combinations(cards, 13):
        layout = best_layout(list(subset), _shared_eval5_cache=shared_cache)
        if layout is None:
            continue
        r = total_royalty(layout)
        if r > best_royalty:
            best_royalty = r
            best = layout

    return best


def _simple_sort_layout(cards: list[Card]) -> Layout:
    """Baseline: sort ascending and slice 3/5/5。"""
    s = sorted(cards, key=lambda c: (c.rank, c.suit))
    return Layout(tuple(s[:3]), tuple(s[3:8]), tuple(s[8:13]))


def _without(cards: list[Card], to_remove: list[Card]) -> list[Card]:
    """Return cards with `to_remove` items dropped (preserve order, drop one each)."""
    rest = list(cards)
    for c in to_remove:
        rest.remove(c)
    return rest


def _candidate_pair_to_front(cards: list[Card]) -> list[Layout]:
    """For each pair of rank ≥ 6, try placing it (with weakest kicker) in front."""
    layouts = []
    by_rank: dict[int, list[Card]] = {}
    for c in cards:
        by_rank.setdefault(c.rank, []).append(c)
    for rank, group in by_rank.items():
        if len(group) < 2 or rank < 6:
            continue
        front_pair = group[:2]
        rest = sorted(_without(cards, front_pair), key=lambda c: (c.rank, c.suit))
        kicker = rest[0]
        layouts.append(
            Layout(
                front=tuple(front_pair + [kicker]),
                middle=tuple(rest[1:6]),
                back=tuple(rest[6:11]),
            )
        )
    return layouts


def _candidate_trips_to_front(cards: list[Card]) -> list[Layout]:
    """For each three-of-a-kind, try placing it in front (huge royalty)."""
    layouts = []
    by_rank: dict[int, list[Card]] = {}
    for c in cards:
        by_rank.setdefault(c.rank, []).append(c)
    for rank, group in by_rank.items():
        if len(group) < 3:
            continue
        front_trips = group[:3]
        rest = sorted(_without(cards, front_trips), key=lambda c: (c.rank, c.suit))
        layouts.append(
            Layout(
                front=tuple(front_trips),
                middle=tuple(rest[:5]),
                back=tuple(rest[5:10]),
            )
        )
    return layouts


def _candidate_flush_to_back(cards: list[Card]) -> list[Layout]:
    """For each suit with 5+ cards, put strongest 5 of that suit in back."""
    layouts = []
    by_suit: dict[int, list[Card]] = {}
    for c in cards:
        by_suit.setdefault(c.suit, []).append(c)
    for suited in by_suit.values():
        if len(suited) < 5:
            continue
        back = sorted(suited, key=lambda c: c.rank, reverse=True)[:5]
        rest = sorted(_without(cards, back), key=lambda c: (c.rank, c.suit))
        layouts.append(
            Layout(
                front=tuple(rest[:3]),
                middle=tuple(rest[3:8]),
                back=tuple(back),
            )
        )
    return layouts


def _candidate_pair_front_flush_back(cards: list[Card]) -> list[Layout]:
    """Combine: pair (≥6) front + flush back + sorted middle."""
    layouts = []
    by_rank: dict[int, list[Card]] = {}
    by_suit: dict[int, list[Card]] = {}
    for c in cards:
        by_rank.setdefault(c.rank, []).append(c)
        by_suit.setdefault(c.suit, []).append(c)
    for rank, group in by_rank.items():
        if len(group) < 2 or rank < 6:
            continue
        front_pair = group[:2]
        for suited in by_suit.values():
            available = [c for c in suited if c not in front_pair]
            if len(available) < 5:
                continue
            back = sorted(available, key=lambda c: c.rank, reverse=True)[:5]
            rest = sorted(
                _without(cards, front_pair + back), key=lambda c: (c.rank, c.suit)
            )
            if len(rest) != 6:
                continue
            kicker = rest[0]
            middle = rest[1:6]
            layouts.append(
                Layout(
                    front=tuple(front_pair + [kicker]),
                    middle=tuple(middle),
                    back=tuple(back),
                )
            )
    return layouts


def _candidate_trips_front_trips_middle(cards: list[Card]) -> list[Layout]:
    """Front trips of rank R1 + middle trips of rank R2 (R2 > R1)."""
    layouts = []
    by_rank: dict[int, list[Card]] = {}
    for c in cards:
        by_rank.setdefault(c.rank, []).append(c)
    trips = [(r, g[:3]) for r, g in by_rank.items() if len(g) >= 3]
    if len(trips) < 2:
        return []
    for r_front, t_front in trips:
        for r_middle, t_middle in trips:
            if r_middle <= r_front:
                continue
            rest = sorted(
                _without(cards, t_front + t_middle), key=lambda c: (c.rank, c.suit)
            )
            if len(rest) < 7:
                continue
            middle_5 = t_middle + rest[:2]  # trips + 2 weak kickers
            back_5 = rest[2:7]              # 5 strongest remaining
            layouts.append(
                Layout(tuple(t_front), tuple(middle_5), tuple(back_5))
            )
    return layouts


def _candidate_pair_front_two_pair_middle(cards: list[Card]) -> list[Layout]:
    """Front pair (≥6) + middle two-pair + back gets 5 sorted leftovers."""
    layouts = []
    by_rank: dict[int, list[Card]] = {}
    for c in cards:
        by_rank.setdefault(c.rank, []).append(c)
    pairs = [(r, g[:2]) for r, g in by_rank.items() if len(g) >= 2]
    if len(pairs) < 3:
        return []
    for fr, fp in pairs:
        if fr < 6:
            continue
        others = [(r, p) for r, p in pairs if r != fr]
        for i, (r1, p1) in enumerate(others):
            for r2, p2 in others[i + 1 :]:
                used = fp + p1 + p2
                rest = sorted(_without(cards, used), key=lambda c: (c.rank, c.suit))
                if len(rest) < 7:
                    continue
                layouts.append(
                    Layout(
                        front=tuple(fp + [rest[0]]),
                        middle=tuple(p1 + p2 + [rest[1]]),
                        back=tuple(rest[2:7]),
                    )
                )
    return layouts


def _candidate_pair_front_double_flush(cards: list[Card]) -> list[Layout]:
    """Front pair (≥6) + middle flush + back flush (need 2 suits each ≥5 cards)."""
    layouts = []
    by_rank: dict[int, list[Card]] = {}
    by_suit: dict[int, list[Card]] = {}
    for c in cards:
        by_rank.setdefault(c.rank, []).append(c)
        by_suit.setdefault(c.suit, []).append(c)
    pairs = [(r, g[:2]) for r, g in by_rank.items() if len(g) >= 2 and r >= 6]
    flush_suits = [s for s, g in by_suit.items() if len(g) >= 5]
    if not pairs or len(flush_suits) < 2:
        return []
    for fr, fp in pairs:
        for s_a in flush_suits:
            avail_a = [c for c in by_suit[s_a] if c not in fp]
            if len(avail_a) < 5:
                continue
            top5_a = sorted(avail_a, key=lambda c: c.rank, reverse=True)[:5]
            for s_b in flush_suits:
                if s_b == s_a:
                    continue
                avail_b = [c for c in by_suit[s_b] if c not in fp and c not in top5_a]
                if len(avail_b) < 5:
                    continue
                top5_b = sorted(avail_b, key=lambda c: c.rank, reverse=True)[:5]
                used = set(fp) | set(top5_a) | set(top5_b)
                remaining = [c for c in cards if c not in used]
                if len(remaining) != 1:
                    continue
                kicker = remaining[0]
                # Try both ord: which flush goes to back vs middle
                for middle_5, back_5 in ((top5_a, top5_b), (top5_b, top5_a)):
                    layouts.append(
                        Layout(
                            front=tuple(fp + [kicker]),
                            middle=tuple(middle_5),
                            back=tuple(back_5),
                        )
                    )
    return layouts


def _grouped_layout(cards: list[Card]) -> Layout:
    """Sort by (count desc, rank desc) so pairs/trips cluster, then slice."""
    counts = Counter(c.rank for c in cards)
    s = sorted(cards, key=lambda c: (-counts[c.rank], -c.rank, c.suit))
    # placing strongest groups first means they go to back; reverse for front first
    s = list(reversed(s))
    return Layout(tuple(s[:3]), tuple(s[3:8]), tuple(s[8:13]))


def _pick_best(candidates: list[Layout], fallback: Layout) -> Layout:
    legal = [c for c in candidates if not is_foul(c)]
    if not legal:
        return fallback
    return max(legal, key=total_royalty)


def heuristic_layout(cards: list[Card]) -> Layout:
    """Multi-candidate heuristic: 列舉幾個結構化擺法挑最佳合法 (max royalty)。

    候選包含 sort-ascending、group-by-rank、把對子/三條放前墩、把同花放後墩、
    以及對子+同花的組合。每個候選 µs 級，總共 ~10-30 個候選。
    若全犯規則退回 sort-ascending baseline。
    """
    if len(cards) != 13:
        raise ValueError(f"heuristic_layout expects 13 cards, got {len(cards)}")

    candidates: list[Layout] = [
        _simple_sort_layout(cards),
        _grouped_layout(cards),
    ]
    candidates.extend(_candidate_pair_to_front(cards))
    candidates.extend(_candidate_trips_to_front(cards))
    candidates.extend(_candidate_flush_to_back(cards))
    candidates.extend(_candidate_pair_front_flush_back(cards))
    candidates.extend(_candidate_trips_front_trips_middle(cards))
    candidates.extend(_candidate_pair_front_two_pair_middle(cards))
    candidates.extend(_candidate_pair_front_double_flush(cards))

    return _pick_best(candidates, fallback=candidates[0])


def heuristic_completion(state, future_cards: list[Card]) -> Layout:
    """把 future_cards 用 heuristic 填滿 state 剩餘空位。

    對「未來牌+剩餘空位」生成幾個候選分配，挑 royalty 最高且不犯規。
    候選：sort ascending、group by rank。
    可能犯規（state 已 placed 的部分可能限制了空間），fallback 用 sort。
    """
    fc = state.front_capacity()
    mc = state.middle_capacity()
    bc = state.back_capacity()
    if fc + mc + bc != len(future_cards):
        raise ValueError(
            f"need {fc + mc + bc} future cards, got {len(future_cards)}"
        )

    candidates: list[Layout] = []

    # Sort ascending → weak to front
    s_asc = sorted(future_cards, key=lambda c: (c.rank, c.suit))
    candidates.append(
        Layout(
            front=state.front + tuple(s_asc[:fc]),
            middle=state.middle + tuple(s_asc[fc : fc + mc]),
            back=state.back + tuple(s_asc[fc + mc :]),
        )
    )

    # Group by rank within future cards (keeps pairs together)
    counts = Counter(c.rank for c in future_cards)
    s_grp = sorted(future_cards, key=lambda c: (counts[c.rank], c.rank, c.suit))
    candidates.append(
        Layout(
            front=state.front + tuple(s_grp[:fc]),
            middle=state.middle + tuple(s_grp[fc : fc + mc]),
            back=state.back + tuple(s_grp[fc + mc :]),
        )
    )

    return _pick_best(candidates, fallback=candidates[0])
