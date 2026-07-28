"""Hand storage for completed hands (verification)."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


HANDS_DIR = Path("hands")


@dataclass
class CompletedHand:
    """A completed hand for verification."""
    hand_id: str
    player: str
    bet: int
    player_cards: list
    dealer_cards: list
    player_value: int
    dealer_value: int
    result: str  # win, lose, push, blackjack
    payout: int
    nonce: str
    commitment: str
    timestamp: str  # ISO format
    
    def to_dict(self) -> dict:
        return {
            "hand_id": self.hand_id,
            "player": self.player,
            "bet": self.bet,
            "player_cards": self.player_cards,
            "dealer_cards": self.dealer_cards,
            "player_value": self.player_value,
            "dealer_value": self.dealer_value,
            "result": self.result,
            "payout": self.payout,
            "nonce": self.nonce,
            "commitment": self.commitment,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CompletedHand":
        return cls(**data)
    
    def save(self) -> None:
        """Save completed hand to file."""
        HANDS_DIR.mkdir(exist_ok=True)
        filepath = HANDS_DIR / f"{self.hand_id}.json"
        
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, hand_id: str) -> Optional["CompletedHand"]:
        """Load completed hand from file."""
        filepath = HANDS_DIR / f"{hand_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def list_all(cls) -> list["CompletedHand"]:
        """List all completed hands."""
        HANDS_DIR.mkdir(exist_ok=True)
        hands = []
        
        for filepath in HANDS_DIR.glob("*.json"):
            with open(filepath, "r") as f:
                data = json.load(f)
                hands.append(cls.from_dict(data))
        
        # Sort by timestamp (newest first)
        hands.sort(key=lambda h: h.timestamp, reverse=True)
        return hands


def verify_hand(hand_id: str, expected_nonce: str) -> bool:
    """Verify a hand's integrity using the nonce."""
    hand = CompletedHand.load(hand_id)
    if not hand:
        return False
    
    if hand.nonce != expected_nonce:
        return False
    
    # The commitment check requires knowing the full shoe order
    # This is a placeholder - the actual verification would need the shoe
    return True