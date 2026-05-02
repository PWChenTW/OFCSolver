from ofc.card import Card
from ofc.hand_eval import HandType, evaluate_3, evaluate_5


def h(*strs: str) -> list[Card]:
    return [Card.from_str(s) for s in strs]


# 5-card tests

def test_royal_flush():
    rank = evaluate_5(h("As", "Ks", "Qs", "Js", "Ts"))
    assert rank == (HandType.ROYAL_FLUSH, (14,))


def test_straight_flush_king_high():
    rank = evaluate_5(h("9s", "Ts", "Js", "Qs", "Ks"))
    assert rank == (HandType.STRAIGHT_FLUSH, (13,))


def test_straight_flush_wheel():
    rank = evaluate_5(h("As", "2s", "3s", "4s", "5s"))
    assert rank == (HandType.STRAIGHT_FLUSH, (5,))


def test_four_of_a_kind():
    rank = evaluate_5(h("As", "Ah", "Ad", "Ac", "Kc"))
    assert rank == (HandType.FOUR_OF_A_KIND, (14, 13))


def test_full_house():
    rank = evaluate_5(h("Ks", "Kh", "Kd", "2c", "2s"))
    assert rank == (HandType.FULL_HOUSE, (13, 2))


def test_flush():
    rank = evaluate_5(h("As", "Ts", "8s", "5s", "2s"))
    assert rank == (HandType.FLUSH, (14, 10, 8, 5, 2))


def test_straight_ace_high():
    rank = evaluate_5(h("As", "Kh", "Qd", "Jc", "Ts"))
    assert rank == (HandType.STRAIGHT, (14,))


def test_straight_wheel():
    rank = evaluate_5(h("As", "2h", "3d", "4c", "5s"))
    assert rank == (HandType.STRAIGHT, (5,))


def test_three_of_a_kind():
    rank = evaluate_5(h("Qs", "Qh", "Qd", "5c", "2s"))
    assert rank == (HandType.THREE_OF_A_KIND, (12, 5, 2))


def test_two_pair():
    rank = evaluate_5(h("Ks", "Kh", "5d", "5c", "9s"))
    assert rank == (HandType.TWO_PAIR, (13, 5, 9))


def test_pair():
    rank = evaluate_5(h("Ks", "Kh", "9d", "5c", "2s"))
    assert rank == (HandType.PAIR, (13, 9, 5, 2))


def test_high_card():
    rank = evaluate_5(h("Ks", "Jh", "8d", "5c", "2s"))
    assert rank == (HandType.HIGH_CARD, (13, 11, 8, 5, 2))


# Tiebreak ordering — using tuple comparison

def test_higher_pair_beats_lower():
    a = evaluate_5(h("As", "Ah", "5d", "3c", "2s"))
    b = evaluate_5(h("Ks", "Kh", "Qd", "Jc", "9s"))
    assert a > b


def test_pair_kicker_breaks_tie():
    a = evaluate_5(h("Ks", "Kh", "Ad", "3c", "2s"))
    b = evaluate_5(h("Kc", "Kd", "Qd", "Jc", "9s"))
    assert a > b


def test_full_house_three_breaks_tie():
    a = evaluate_5(h("Ks", "Kh", "Kd", "2c", "2s"))
    b = evaluate_5(h("Qs", "Qh", "Qd", "As", "Ah"))
    assert a > b


def test_straight_flush_beats_four_of_a_kind():
    sf = evaluate_5(h("9s", "Ts", "Js", "Qs", "Ks"))
    quads = evaluate_5(h("As", "Ah", "Ad", "Ac", "Kc"))
    assert sf > quads


def test_wheel_straight_loses_to_six_high_straight():
    wheel = evaluate_5(h("As", "2h", "3d", "4c", "5s"))
    six_high = evaluate_5(h("2s", "3h", "4d", "5c", "6s"))
    assert six_high > wheel


# 3-card tests (front)

def test_front_three_of_a_kind():
    rank = evaluate_3(h("As", "Ah", "Ad"))
    assert rank == (HandType.THREE_OF_A_KIND, (14,))


def test_front_pair():
    rank = evaluate_3(h("Ks", "Kh", "5d"))
    assert rank == (HandType.PAIR, (13, 5))


def test_front_high_card():
    rank = evaluate_3(h("As", "Kh", "5d"))
    assert rank == (HandType.HIGH_CARD, (14, 13, 5))


def test_front_pair_beats_high_card():
    p = evaluate_3(h("2s", "2h", "3d"))
    hc = evaluate_3(h("As", "Kh", "Qd"))
    assert p > hc


def test_front_pair_kicker_tiebreak():
    a = evaluate_3(h("Ks", "Kh", "Ad"))
    b = evaluate_3(h("Kc", "Kd", "Qd"))
    assert a > b
