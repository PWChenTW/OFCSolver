from ofc.layout import Layout, is_foul
from ofc.scoring import settle


def L(front, middle, back) -> Layout:
    return Layout.from_strs(front, middle, back)


def assert_disjoint(p1: Layout, p2: Layout) -> None:
    cards1 = set(p1.front + p1.middle + p1.back)
    cards2 = set(p2.front + p2.middle + p2.back)
    assert not (cards1 & cards2), f"P1/P2 share cards: {cards1 & cards2}"


def test_scoop_no_royalty():
    p1 = L(
        ["3d", "4c", "5s"],                  # high card 5
        ["5h", "5c", "6d", "7s", "8c"],     # pair 5 (no middle royalty)
        ["9h", "9c", "Th", "Td", "Js"],     # two pair TT99 (no back royalty)
    )
    p2 = L(
        ["2s", "3s", "4d"],                  # high card 4
        ["4s", "6s", "8h", "Tc", "Jh"],     # high card J
        ["Kc", "Kh", "7c", "8d", "Qd"],     # pair K
    )
    assert not is_foul(p1)
    assert not is_foul(p2)
    assert_disjoint(p1, p2)
    # P1 wins all → +3 lines + 3 scoop, royalties 0
    assert settle(p1, p2) == 6


def test_two_to_one_with_royalties():
    p1 = L(
        ["As", "Ah", "2c"],                  # AA → 9
        ["5s", "5h", "5d", "7c", "8c"],     # trips 5 → middle 2
        ["9h", "9c", "9d", "Th", "Td"],     # full house → back 6
    )
    p2 = L(
        ["Ks", "Kh", "2d"],                  # KK → 8
        ["6s", "6h", "6c", "7s", "8s"],     # trips 6 → middle 2
        ["Jc", "Jd", "Js", "Jh", "4c"],     # quads J → back 10
    )
    assert not is_foul(p1)
    assert not is_foul(p2)
    assert_disjoint(p1, p2)
    # Lines: front +1, middle -1, back -1 → -1
    # Royalty: 17 - 20 = -3
    # Net = -4
    assert settle(p1, p2) == -4


def test_p1_fouls():
    p1 = L(
        ["As", "Ah", "Ad"],                  # trips A
        ["Ks", "Kh", "2c", "3d", "4c"],     # pair K (foul: trips > pair)
        ["Qs", "Qh", "Qd", "9c", "9h"],
    )
    p2 = L(
        ["3h", "4h", "5d"],                  # high card 5
        ["6c", "6d", "6h", "8s", "Js"],     # trips 6 → middle 2
        ["Tc", "Td", "Th", "7d", "7h"],     # full house TTT77 → back 6
    )
    assert is_foul(p1)
    assert not is_foul(p2)
    assert_disjoint(p1, p2)
    # P2 royalty = 8; net = -(6 + 8) = -14
    assert settle(p1, p2) == -14


def test_p2_fouls():
    p1 = L(
        ["3h", "4h", "5d"],
        ["6c", "6d", "6h", "8s", "Js"],
        ["Tc", "Td", "Th", "7d", "7h"],
    )
    p2 = L(
        ["As", "Ah", "Ad"],
        ["Ks", "Kh", "2c", "3d", "4c"],
        ["Qs", "Qh", "Qd", "9c", "9h"],
    )
    assert not is_foul(p1)
    assert is_foul(p2)
    assert_disjoint(p1, p2)
    assert settle(p1, p2) == 14


def test_both_foul():
    p1 = L(
        ["As", "Ah", "Ad"],
        ["Ks", "Kh", "2c", "3d", "4c"],
        ["Qs", "Qh", "Qd", "9c", "9h"],
    )
    p2 = L(
        ["Kd", "Kc", "Js"],                  # pair K
        ["Qc", "Jh", "5c", "6c", "7d"],     # high card Q (foul: pair > high card)
        ["8s", "8h", "8d", "9d", "Th"],
    )
    assert is_foul(p1)
    assert is_foul(p2)
    assert_disjoint(p1, p2)
    assert settle(p1, p2) == 0


def test_zero_sum_swap():
    p1 = L(
        ["As", "Ah", "2c"],
        ["5s", "5h", "5d", "7c", "8c"],
        ["9h", "9c", "9d", "Th", "Td"],
    )
    p2 = L(
        ["Ks", "Kh", "2d"],
        ["6s", "6h", "6c", "7s", "8s"],
        ["Jc", "Jd", "Js", "Jh", "4c"],
    )
    assert settle(p1, p2) == -settle(p2, p1)


def test_no_scoop_when_one_line_tied():
    p1 = L(
        ["7s", "5d", "2c"],                  # high card 7
        ["Qs", "Qd", "8c", "6h", "4h"],     # pair Q (kickers 8, 6, 4)
        ["Ad", "As", "Ah", "5h", "5c"],     # full house AAA55 → 6
    )
    p2 = L(
        ["6d", "4d", "2d"],                  # high card 6
        ["Qh", "Qc", "8s", "6c", "4c"],     # pair Q same kickers — tied
        ["Tc", "Td", "9s", "9d", "9c"],     # full house 999TT → 6
    )
    assert not is_foul(p1)
    assert not is_foul(p2)
    assert_disjoint(p1, p2)
    # Lines: front +1, middle 0 (tie), back +1 → +2 (no scoop)
    # Royalty: 6 - 6 = 0
    # Net = +2
    assert settle(p1, p2) == 2
