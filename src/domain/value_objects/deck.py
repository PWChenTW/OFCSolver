"""Deck Value Object - Placeholder"""
from typing import List
from ..base import ValueObject
from .card import Card

class Deck(ValueObject):
    """Deck placeholder."""
    def __init__(self):
        self._cards = Card.create_deck()
    
    def remaining_cards(self) -> List[Card]:
        return self._cards.copy()
    
    def has_card(self, card: Card) -> bool:
        return card in self._cards
    
    def remove_card(self, card: Card) -> None:
        if card in self._cards:
            self._cards.remove(card)
    
    def deal_cards(self, count: int) -> List[Card]:
        dealt = self._cards[:count]
        self._cards = self._cards[count:]
        return dealt