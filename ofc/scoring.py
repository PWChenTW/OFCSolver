from .layout import Layout, is_foul, total_royalty


def settle(p1: Layout, p2: Layout) -> int:
    """從 P1 視角的淨分（P1 - P2）。

    規則：
    - 雙方犯規：0
    - 一方犯規：犯規方輸 6 分（3 墩 + 3 scoop），對手仍拿自己的 royalty
    - 都不犯規：每墩比較 ±1，全贏額外 +3，雙方各自累計 royalty
    """
    p1_foul = is_foul(p1)
    p2_foul = is_foul(p2)

    if p1_foul and p2_foul:
        return 0
    if p1_foul:
        return -(6 + total_royalty(p2))
    if p2_foul:
        return 6 + total_royalty(p1)

    rows = [
        (p1.front_rank(), p2.front_rank()),
        (p1.middle_rank(), p2.middle_rank()),
        (p1.back_rank(), p2.back_rank()),
    ]

    line_score = 0
    p1_wins = 0
    p2_wins = 0
    for a, b in rows:
        if a > b:
            line_score += 1
            p1_wins += 1
        elif a < b:
            line_score -= 1
            p2_wins += 1

    if p1_wins == 3:
        line_score += 3
    elif p2_wins == 3:
        line_score -= 3

    royalty_diff = total_royalty(p1) - total_royalty(p2)
    return line_score + royalty_diff
