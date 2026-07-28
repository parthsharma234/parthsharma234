"""Six-deck shoe with provably fair generation."""
import hashlib
import json
import random
import secrets
from typing import List, Optional
from .cards import Card, Rank, Suit


class Shoe:
    NUM_DECKS = 6
    
    def __init__(self, cards: Optional[List[Card]] = None):
        self._cards = cards if cards is not None else []
        self._original_cards: Optional[List[Card]] = cards.copy() if cards else None
        self._nonce: Optional[str] = None
    
    @property
    def remaining(self) -> int:
        return len(self._cards)
    
    def deal(self) -> Card:
        if not self._cards:
            raise RuntimeError("Shoe is empty")
        return self._cards.pop(0)
    
    def is_empty(self) -> bool:
        return len(self._cards) == 0
    
    @classmethod
    def generate_fresh(cls) -> tuple["Shoe", str]:
        """Generate fresh shuffled shoe with provably fair commitment."""
        nonce = secrets.token_hex(16)
        seed_bytes = hashlib.sha256(nonce.encode()).digest()
        seed = int.from_bytes(seed_bytes[:4], 'big')
        
        all_cards = []
        for _ in range(cls.NUM_DECKS):
            for suit in Suit:
                for rank in Rank:
                    all_cards.append(Card(rank, suit))
        
        rng = random.Random(seed)
        rng.shuffle(all_cards)
        
        shoe = cls(all_cards)
        shoe._nonce = nonce
        
        shoe_json = json.dumps([c.to_dict() for c in all_cards], sort_keys=True)
        commitment = hashlib.sha256((nonce + shoe_json).encode()).hexdigest()
        
        return shoe, commitment
    
    def verify_commitment(self, commitment: str) -> bool:
        if self._nonce is None:
            return False
        # Use original cards (before any were dealt)
        cards_to_verify = self._original_cards if self._original_cards else self._cards
        shoe_json = json.dumps([c.to_dict() for c in cards_to_verify], sort_keys=True)
        computed = hashlib.sha256((self._nonce + shoe_json).encode()).hexdigest()
        return computed == commitment
    
    def reveal(self) -> dict:
        # Use original cards to reveal the full shoe
        cards_to_reveal = self._original_cards if self._original_cards else self._cards
        return {"nonce": self._nonce, "cards": [c.to_dict() for c in cards_to_reveal]}
    
    def to_dict(self) -> dict:
        return {
            "remaining": [c.to_dict() for c in self._cards],
            "original": [c.to_dict() for c in self._original_cards] if self._original_cards else None,
            "nonce": self._nonce,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Shoe":
        cards = [Card.from_dict(c) for c in data.get("remaining", [])]
        shoe = cls(cards)
        if data.get("original"):
            shoe._original_cards = [Card.from_dict(c) for c in data["original"]]
        shoe._nonce = data.get("nonce")
        return shoe