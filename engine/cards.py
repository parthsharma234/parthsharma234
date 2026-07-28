"""Card representations for blackjack."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank(Enum):
    ACE = ("A", [1, 11])
    TWO = ("2", [2])
    THREE = ("3", [3])
    FOUR = ("4", [4])
    FIVE = ("5", [5])
    SIX = ("6", [6])
    SEVEN = ("7", [7])
    EIGHT = ("8", [8])
    NINE = ("9", [9])
    TEN = ("10", [10])
    JACK = ("J", [10])
    QUEEN = ("Q", [10])
    KING = ("K", [10])

    def __init__(self, symbol: str, values: list[int]):
        self.symbol = symbol
        self.values = values

    @property
    def is_ten_card(self) -> bool:
        return self in (Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING)


@dataclass
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.symbol}{self.suit.value}"

    @property
    def is_ace(self) -> bool:
        return self.rank == Rank.ACE

    def to_dict(self) -> dict:
        return {"rank": self.rank.symbol, "suit": self.suit.value}

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(Rank(data["rank"]), Suit(data["suit"]))