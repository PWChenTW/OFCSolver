from ofc.card import Card, Rank, Suit, full_deck


def test_card_str_roundtrip():
    for s in ["As", "2h", "Td", "Kc", "9s"]:
        assert str(Card.from_str(s)) == s


def test_full_deck_unique():
    deck = full_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52


def test_rank_values():
    assert Rank.ACE > Rank.KING > Rank.TWO
    assert int(Rank.TEN) == 10


def test_card_equality():
    assert Card(Rank.ACE, Suit.SPADES) == Card.from_str("As")
    assert Card.from_str("As") != Card.from_str("Ah")
