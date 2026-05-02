import pytest

from ofc.layout import (
    Layout,
    back_royalty,
    front_royalty,
    is_foul,
    middle_royalty,
    total_royalty,
)


def L(front, middle, back) -> Layout:
    return Layout.from_strs(front, middle, back)


# Layout validation

def test_layout_rejects_wrong_front_size():
    with pytest.raises(ValueError, match="front"):
        Layout.from_strs(["As", "Ks"], ["2h", "3h", "4h", "5h", "6h"], ["7d", "8d", "9d", "Td", "Jd"])


def test_layout_rejects_wrong_middle_size():
    with pytest.raises(ValueError, match="middle"):
        Layout.from_strs(["As", "Ks", "Qs"], ["2h", "3h", "4h"], ["7d", "8d", "9d", "Td", "Jd"])


def test_layout_rejects_duplicates():
    with pytest.raises(ValueError, match="duplicate"):
        Layout.from_strs(["As", "Ks", "Qs"], ["As", "3h", "4h", "5h", "6h"], ["7d", "8d", "9d", "Td", "Jd"])


# Foul detection

def test_legal_layout_not_foul():
    layout = L(
        ["2c", "3d", "4h"],
        ["5s", "5h", "6c", "6d", "7c"],
        ["As", "Ah", "Ad", "Ks", "Kh"],
    )
    assert is_foul(layout) is False


def test_foul_when_middle_beats_back():
    layout = L(
        ["2c", "3d", "4h"],
        ["As", "Ah", "Ad", "Ks", "Kh"],  # full house aces
        ["5s", "5h", "6c", "6d", "7c"],   # two pair
    )
    assert is_foul(layout) is True


def test_foul_when_front_beats_middle():
    layout = L(
        ["As", "Ah", "Ad"],                # trips aces (front)
        ["Ks", "Kh", "2c", "3d", "4c"],   # pair kings (middle)
        ["Qs", "Qh", "Qd", "9c", "9h"],   # full house
    )
    assert is_foul(layout) is True


def test_equal_strength_not_foul():
    # front pair K, middle pair K — equal pair rank, allowed
    layout = L(
        ["Ks", "Kh", "2c"],
        ["Kc", "Kd", "5h", "4h", "3h"],
        ["As", "Ah", "Ad", "Ac", "9c"],
    )
    assert is_foul(layout) is False


# Royalty — front

def test_front_pair_royalty():
    from ofc.hand_eval import evaluate_3, HandType
    assert front_royalty((HandType.PAIR, (5, 2))) == 0   # 55 → 0
    assert front_royalty((HandType.PAIR, (6, 2))) == 1   # 66 → 1
    assert front_royalty((HandType.PAIR, (10, 2))) == 5  # TT → 5
    assert front_royalty((HandType.PAIR, (14, 2))) == 9  # AA → 9


def test_front_trips_royalty():
    from ofc.hand_eval import HandType
    assert front_royalty((HandType.THREE_OF_A_KIND, (2,))) == 10
    assert front_royalty((HandType.THREE_OF_A_KIND, (10,))) == 18
    assert front_royalty((HandType.THREE_OF_A_KIND, (14,))) == 22


def test_front_high_card_no_royalty():
    from ofc.hand_eval import HandType
    assert front_royalty((HandType.HIGH_CARD, (14, 13, 12))) == 0


# Royalty — middle

def test_middle_royalties():
    from ofc.hand_eval import HandType
    assert middle_royalty((HandType.HIGH_CARD, (14,))) == 0
    assert middle_royalty((HandType.PAIR, (14, 2, 3, 4))) == 0
    assert middle_royalty((HandType.TWO_PAIR, (14, 13, 2))) == 0
    assert middle_royalty((HandType.THREE_OF_A_KIND, (5,))) == 2
    assert middle_royalty((HandType.STRAIGHT, (10,))) == 4
    assert middle_royalty((HandType.FLUSH, (14,))) == 8
    assert middle_royalty((HandType.FULL_HOUSE, (3, 2))) == 12
    assert middle_royalty((HandType.FOUR_OF_A_KIND, (5, 2))) == 20
    assert middle_royalty((HandType.STRAIGHT_FLUSH, (9,))) == 30
    assert middle_royalty((HandType.ROYAL_FLUSH, (14,))) == 50


# Royalty — back

def test_back_royalties():
    from ofc.hand_eval import HandType
    assert back_royalty((HandType.THREE_OF_A_KIND, (5,))) == 0
    assert back_royalty((HandType.STRAIGHT, (10,))) == 2
    assert back_royalty((HandType.FLUSH, (14,))) == 4
    assert back_royalty((HandType.FULL_HOUSE, (3, 2))) == 6
    assert back_royalty((HandType.FOUR_OF_A_KIND, (5, 2))) == 10
    assert back_royalty((HandType.STRAIGHT_FLUSH, (9,))) == 15
    assert back_royalty((HandType.ROYAL_FLUSH, (14,))) == 25


# Total royalty integration

def test_total_royalty_sums_correctly():
    # Front QQ + 2c → 7; Middle full house 33355 → 12; Back royal flush diamonds → 25
    layout = L(
        ["Qs", "Qh", "2c"],
        ["3s", "3h", "3d", "5c", "5h"],
        ["Ad", "Kd", "Qd", "Jd", "Td"],
    )
    assert total_royalty(layout) == 7 + 12 + 25


def test_foul_zeroes_royalty():
    layout = L(
        ["As", "Ah", "Ad"],
        ["Ks", "Kh", "2c", "3d", "4c"],
        ["Qs", "Qh", "Qd", "9c", "9h"],
    )
    assert is_foul(layout)
    assert total_royalty(layout) == 0
