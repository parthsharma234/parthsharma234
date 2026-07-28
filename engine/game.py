"""Main game logic - ties shoe, hands, and actions together."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from .shoe import Shoe
from .hand import Hand, DealerHand
from .cards import Card


class GameAction(Enum):
    HIT = "hit"
    STAND = "stand"
    DOUBLE = "double"


class GameResult(Enum):
    WIN = "win"
    LOSE = "lose"
    PUSH = "push"
    BLACKJACK = "blackjack"


@dataclass
class GameState:
    """Complete game state for serialization."""
    player_hand: Hand = field(default_factory=Hand)
    dealer_hand: DealerHand = field(default_factory=DealerHand)
    shoe: Optional[Shoe] = None
    commitment: Optional[str] = None
    bet: int = 0
    player: str = ""
    hand_id: str = ""
    phase: str = "betting"  # betting, player_turn, dealer_turn, resolved
    message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "player_hand": self.player_hand.to_dict(),
            "dealer_hand": self.dealer_hand.to_dict(),
            "shoe": self.shoe.to_dict() if self.shoe else None,
            "commitment": self.commitment,
            "bet": self.bet,
            "player": self.player,
            "hand_id": self.hand_id,
            "phase": self.phase,
            "message": self.message,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        state = cls()
        state.player_hand = Hand.from_dict(data.get("player_hand", {}))
        state.dealer_hand = DealerHand.from_dict(data.get("dealer_hand", {}))
        if data.get("shoe"):
            state.shoe = Shoe.from_dict(data["shoe"])
        state.commitment = data.get("commitment")
        state.bet = data.get("bet", 0)
        state.player = data.get("player", "")
        state.hand_id = data.get("hand_id", "")
        state.phase = data.get("phase", "betting")
        state.message = data.get("message", "")
        return state


class BlackjackEngine:
    """Pure game logic - no GitHub awareness."""
    
    STARTING_CHIPS = 1000
    BET_PRESETS = [25, 50, 100, 250]
    
    def __init__(self):
        self.state = GameState()
    
    def start_hand(self, player: str, bet: int, hand_id: str) -> GameState:
        """Start a new hand with fresh shoe."""
        if bet not in self.BET_PRESETS:
            raise ValueError(f"Bet must be one of {self.BET_PRESETS}")
        
        shoe, commitment = Shoe.generate_fresh()
        
        self.state = GameState(
            shoe=shoe,
            commitment=commitment,
            bet=bet,
            player=player,
            hand_id=hand_id,
            phase="player_turn",
            message=f"Hand #{hand_id} — Bet: {bet} chips",
        )
        
        # Deal initial cards (player, dealer, player, dealer)
        self.state.player_hand.add_card(shoe.deal())
        self.state.dealer_hand.add_card(shoe.deal())
        self.state.player_hand.add_card(shoe.deal())
        self.state.dealer_hand.add_card(shoe.deal())
        
        # Check for blackjack
        if self.state.player_hand.is_blackjack:
            self._resolve_blackjack()
        
        return self.state
    
    def hit(self) -> GameState:
        """Player hits."""
        if self.state.phase != "player_turn":
            raise RuntimeError("Not your turn")
        if not self.state.player_hand.can_hit:
            raise RuntimeError("Cannot hit")
        
        card = self.state.shoe.deal()
        self.state.player_hand.add_card(card)
        self.state.message = f"You drew {card}"
        
        if self.state.player_hand.is_bust:
            self._resolve_bust()
        
        return self.state
    
    def stand(self) -> GameState:
        """Player stands."""
        if self.state.phase != "player_turn":
            raise RuntimeError("Not your turn")
        
        self.state.phase = "dealer_turn"
        self.state.dealer_hand.reveal_hole_card()
        self._play_dealer()
        self._resolve()
        
        return self.state
    
    def double(self) -> GameState:
        """Player doubles down."""
        if self.state.phase != "player_turn":
            raise RuntimeError("Not your turn")
        if not self.state.player_hand.can_double:
            raise RuntimeError("Cannot double")
        
        # Double the bet, get exactly one card
        self.state.player_hand.is_double = True
        self.state.player_hand.bet = self.state.bet * 2
        self.state.bet = self.state.bet * 2
        
        card = self.state.shoe.deal()
        self.state.player_hand.add_card(card)
        self.state.message = f"Double down! You drew {card}"
        
        if self.state.player_hand.is_bust:
            self._resolve_bust()
        else:
            self.state.phase = "dealer_turn"
            self.state.dealer_hand.reveal_hole_card()
            self._play_dealer()
            self._resolve()
        
        return self.state
    
    def _play_dealer(self) -> None:
        """Dealer plays: hit on soft 17, stand on all 17."""
        while self.state.dealer_hand.should_hit:
            card = self.state.shoe.deal()
            self.state.dealer_hand.add_card(card)
    
    def _resolve_blackjack(self) -> None:
        """Handle blackjack outcome."""
        self.state.phase = "resolved"
        
        if self.state.dealer_hand.is_blackjack:
            # Both have blackjack - push
            self.state.player_hand.result = "push"
            self.state.player_hand.payout = 0
            self.state.message = "Both have blackjack! Push."
        else:
            # Blackjack pays 3:2
            self.state.player_hand.result = "blackjack"
            payout = int(self.state.bet * 1.5)
            self.state.player_hand.payout = payout
            self.state.message = f"Blackjack! You win {payout} chips (3:2)"
    
    def _resolve_bust(self) -> None:
        """Handle player bust."""
        self.state.phase = "resolved"
        self.state.player_hand.result = "lose"
        self.state.player_hand.payout = -self.state.bet
        self.state.message = f"Bust! You lose {self.state.bet} chips"
    
    def _resolve(self) -> None:
        """Resolve the hand against dealer."""
        self.state.phase = "resolved"
        
        player_val = self.state.player_hand.value
        dealer_val = self.state.dealer_hand.value
        
        if self.state.dealer_hand.is_bust:
            self.state.player_hand.result = "win"
            payout = self.state.bet
            self.state.player_hand.payout = payout
            self.state.message = f"Dealer busts! You win {payout} chips"
        elif player_val > dealer_val:
            self.state.player_hand.result = "win"
            payout = self.state.bet
            self.state.player_hand.payout = payout
            self.state.message = f"You win {payout} chips!"
        elif player_val < dealer_val:
            self.state.player_hand.result = "lose"
            self.state.player_hand.payout = -self.state.bet
            self.state.message = f"Dealer wins. You lose {self.state.bet} chips"
        else:
            self.state.player_hand.result = "push"
            self.state.player_hand.payout = 0
            self.state.message = "Push!"
        
        self.state.player_hand.is_resolved = True
    
    def get_reveal(self) -> dict:
        """Full reveal for verification."""
        return {
            "hand_id": self.state.hand_id,
            "player": self.state.player,
            "bet": self.state.bet,
            "player_hand": self.state.player_hand.to_dict(),
            "dealer_hand": self.state.dealer_hand.to_dict(),
            "shoe_reveal": self.state.shoe.reveal() if self.shoe else None,
            "commitment": self.state.commitment,
        }
    
    @property
    def shoe(self) -> Optional[Shoe]:
        return self.state.shoe