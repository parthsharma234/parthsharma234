"""Player state management."""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from .game import GameState


PLAYERS_DIR = Path("players")


@dataclass
class PlayerState:
    """Complete player state for serialization."""
    username: str
    chips: int = 1000
    hands_played: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    blackjacks: int = 0
    current_streak: int = 0
    best_streak: int = 0
    rebuys: int = 0
    # In-progress hand (None if not playing)
    active_hand: Optional[GameState] = None
    
    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "chips": self.chips,
            "hands_played": self.hands_played,
            "wins": self.wins,
            "losses": self.losses,
            "pushes": self.pushes,
            "blackjacks": self.blackjacks,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "rebuys": self.rebuys,
            "active_hand": self.active_hand.to_dict() if self.active_hand else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PlayerState":
        state = cls(username=data.get("username", ""))
        state.chips = data.get("chips", 1000)
        state.hands_played = data.get("hands_played", 0)
        state.wins = data.get("wins", 0)
        state.losses = data.get("losses", 0)
        state.pushes = data.get("pushes", 0)
        state.blackjacks = data.get("blackjacks", 0)
        state.current_streak = data.get("current_streak", 0)
        state.best_streak = data.get("best_streak", 0)
        state.rebuys = data.get("rebuys", 0)
        if data.get("active_hand"):
            state.active_hand = GameState.from_dict(data["active_hand"])
        return state
    
    @classmethod
    def load(cls, username: str) -> "PlayerState":
        """Load player from file, or create new player if not exists."""
        PLAYERS_DIR.mkdir(exist_ok=True)
        filepath = PLAYERS_DIR / f"{username}.json"
        
        if filepath.exists():
            with open(filepath, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        
        # New player
        return cls(username=username)
    
    def save(self) -> None:
        """Atomically save player state to file."""
        PLAYERS_DIR.mkdir(exist_ok=True)
        filepath = PLAYERS_DIR / f"{self.username}.json"
        temp_filepath = filepath.with_suffix(".tmp")
        
        with open(temp_filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        
        # Atomic rename
        temp_filepath.replace(filepath)
    
    @property
    def has_active_hand(self) -> bool:
        return self.active_hand is not None and self.active_hand.phase != "resolved"
    
    def can_play(self, bet: int) -> bool:
        """Check if player can start a new hand."""
        # Can't have an active hand
        if self.has_active_hand:
            return False
        # Must have enough chips
        if self.chips < bet:
            return False
        return True
    
    def start_hand(self, game_state: GameState, bet: int) -> None:
        """Start a new hand for the player."""
        self.active_hand = game_state
        self.chips -= bet
    
    def resolve_hand(self, payout: int, result: str) -> None:
        """Resolve the active hand and update stats."""
        if not self.active_hand:
            return
        
        self.hands_played += 1
        self.chips += payout
        
        if result == "win":
            self.wins += 1
            self.current_streak += 1
            if self.current_streak > self.best_streak:
                self.best_streak = self.current_streak
        elif result == "lose":
            self.losses += 1
            self.current_streak = 0
        elif result == "push":
            self.pushes += 1
            # Streak continues on push
        elif result == "blackjack":
            self.blackjacks += 1
            self.wins += 1
            self.current_streak += 1
            if self.current_streak > self.best_streak:
                self.best_streak = self.current_streak
        
        # Clear active hand
        self.active_hand = None
        
        # Check for rebuy
        if self.chips <= 0:
            self.chips = 1000
            self.rebuys += 1
    
    def cancel_hand(self) -> None:
        """Cancel active hand and refund bet."""
        if self.active_hand:
            self.chips += self.active_hand.bet
            self.active_hand = None


class StatsManager:
    """Aggregate house statistics."""
    
    STATS_FILE = Path("stats.json")
    
    def __init__(self):
        self.total_hands = 0
        self.unique_players = 0
        self.chips_won = 0
        self.chips_lost = 0
        self.biggest_win = 0
        self.longest_streak = 0
        self._player_set: set = set()
        self._load()
    
    def _load(self) -> None:
        if self.STATS_FILE.exists():
            with open(self.STATS_FILE, "r") as f:
                data = json.load(f)
                self.total_hands = data.get("total_hands", 0)
                self._player_set = set(data.get("players", []))
                self.unique_players = len(self._player_set)
                self.chips_won = data.get("chips_won", 0)
                self.chips_lost = data.get("chips_lost", 0)
                self.biggest_win = data.get("biggest_win", 0)
                self.longest_streak = data.get("longest_streak", 0)
    
    def save(self) -> None:
        with open(self.STATS_FILE, "w") as f:
            json.dump({
                "total_hands": self.total_hands,
                "players": list(self._player_set),
                "chips_won": self.chips_won,
                "chips_lost": self.chips_lost,
                "biggest_win": self.biggest_win,
                "longest_streak": self.longest_streak,
            }, f, indent=2)
    
    def record_hand(self, player: str, payout: int, streak: int) -> None:
        """Record a completed hand."""
        self.total_hands += 1
        self._player_set.add(player)
        self.unique_players = len(self._player_set)
        
        if payout > 0:
            self.chips_won += payout
        else:
            self.chips_lost += abs(payout)
        
        if payout > self.biggest_win:
            self.biggest_win = payout
        
        if streak > self.longest_streak:
            self.longest_streak = streak
        
        self.save()
    
    @property
    def house_edge_theoretical(self) -> float:
        """Theoretical house edge (0.5% for basic strategy)."""
        return 0.5
    
    @property
    def house_edge_realized(self) -> float:
        """Realized house edge based on actual results."""
        if self.total_hands == 0:
            return 0.0
        total_wagered = self.chips_won + self.chips_lost
        if total_wagered == 0:
            return 0.0
        return (self.chips_lost - self.chips_won) / total_wagered * 100
    
    def to_dict(self) -> dict:
        return {
            "total_hands": self.total_hands,
            "unique_players": self.unique_players,
            "chips_won": self.chips_won,
            "chips_lost": self.chips_lost,
            "biggest_win": self.biggest_win,
            "longest_streak": self.longest_streak,
            "house_edge_realized": round(self.house_edge_realized, 2),
            "house_edge_theoretical": self.house_edge_theoretical,
        }