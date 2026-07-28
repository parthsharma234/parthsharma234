# parthsharma234

Computer Engineering at Purdue, class of 2030. I work on embedded systems and the software around them, most recently a magnetometer payload that flew on a NASA Student Launch rocket. Looking for research in embedded instrumentation or robotics.

---

## 🃏 Blackjack

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║  BLACKJACK                                                      ║
    ║  ═══════════════════════════════════════════════════════════  ║
    ║                                                               ║
    ║     DEALER                      YOU                          ║
    ║    ┌───────┐                   ┌───────┐ ┌───────┐          ║
    ║    │  ♠ A  │                   │  ♥ K  │ │  ♦ 7  │          ║
    ║    │       │                   │       │ │       │          ║
    ║    │       │                   │       │ │       │          ║
    ║    │   A   │                   │   K   │ │   7   │          ║
    ║    └───────┘                   └───────┘ └───────┘          ║
    ║                                                               ║
    ║    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
    ║                                                               ║
    ║    [HIT]  [STAND]  [DOUBLE]                                   ║
    ║                                                               ║
    ║    Bet: 25  |  Chips: 1000  |  Hand: #1A2B                    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

### How to Play

1. **[Create an Issue](https://github.com/parthsharma234/parthsharma234/issues/new?title=blackjack&body=bet%3A+25)** to start a hand
2. The dealer deals your cards (hidden from the shoe)
3. Comment **HIT**, **STAND**, or **DOUBLE** to play
4. The bot updates your table in place

### Rules

- Dealer stands on all 17
- Blackjack pays 3:2
- Double on first two cards only
- No splits, no insurance
- Fresh 6-deck shoe every hand

### Provably Fair

Every hand has a cryptographic commitment. After resolution, the full shoe is revealed so you can verify the deal was fixed before you acted.