"""Hand representation and evaluation."""
from dataclasses import dataclass, field
from typing import List, Optional
from .cards import Card


@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)
    bet: int = 0
    is_double: bool = False
    is_resolved: bool = False
    result: Optional[str] = None
    payout: int = 0
    
    @property
    def is_blackjack(self) -> bool:
        if len(self.cards) != 2:
            return False
        return any(c.is_ace for c in self.cards) and any(c.rank.is_ten_card for c in self.cards)
    
    @property
    def is_bust(self) -> bool:
        return self.value > 21
    
    @property
    def value(self) -> int:
        values = [0]
        for card in self.cards:
            if card.is_ace:
                new_values = []
                for v in values:
                    new_values.extend([v + 1, v + 11])
                values = new_values
            else:
                values = [v + card.rank.values[0] for v in values]
        valid = [v for v in values if v <= 21]
        return max(valid) if valid else min(values)
    
    @property
    def can_hit(self) -> bool:
        return not self.is_resolved and not self.is_double
    
    @property
    def can_double(self) -> bool:
        return len(self.cards) == 2 and not self.is_resolved and not self.is_double
    
    def add_card(self, card: Card) -> None:
        self.cards.append(card)
    
    def to_dict(self) -> dict:
        return {
            "cards": [c.to_dict() for c in self.cards],
            "bet": self.bet,
            "is_double": self.is_double,
            "is_resolved": self.is_resolved,
            "result": self.result,
            "payout": self.payout,
            "value": self.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Hand":
        hand = cls(cards=[Card.from_dict(c) for c in data.get("cards", [])], bet=data.get("bet", 0))
        hand.is_double = data.get("is_double", False)
        hand.is_resolved = data.get("is_resolved", False)
        hand.result = data.get("result")
        hand.payout = data.get("payout", 0)
        return hand


@dataclass
class DealerHand(Hand):
    hole_card_hidden: bool = True
    
    def reveal_hole_card(self) -> None:
        self.hole_card_hidden = False
    
    @property
    def visible_value(self) -> int:
        if not self.cards:
            return 0
        if self.hole_card_hidden:
            first = self.cards[0]
            return 11 if first.is_ace else first.rank.values[0]
        return self.value
    
    @property
    def should_hit(self) -> bool:
        # Dealer stands on all 17 (including soft 17)
        return self.value <= 16
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["hole_card_hidden"] = self.hole_card_hidden
        data["visible_value"] = self.visible_value
        return data