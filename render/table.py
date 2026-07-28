"""ASCII table renderer for hands."""
from engine.game import GameState
from engine.cards import Card


def render_card(card: Card) -> str:
    """Render a single card as ASCII."""
    symbol = card.rank.symbol
    suit = card.suit.value
    
    # Card dimensions
    width = 7
    
    lines = [
        f"┌{'─' * width}┐",
        f"│{symbol}{' ' * (width - 1)}│",
        f"│{' ' * width}│",
        f"│{' ' * (width // 2)}{suit}{' ' * (width - width // 2 - 1)}│",
        f"│{' ' * width}│",
        f"│{' ' * (width - 1)}{symbol}│",
        f"└{'─' * width}┘",
    ]
    return "\n".join(lines)


def render_hand(cards: list[Card], show_all: bool = False) -> str:
    """Render multiple cards side by side."""
    if not cards:
        return "  (empty)  "
    
    card_lines = [render_card(c).split("\n") for c in cards]
    
    result = []
    for i in range(len(card_lines[0])):
        line = " ".join(card[i] for card in card_lines)
        result.append(line)
    
    return "\n".join(result)


def render_hand_table(state: GameState) -> str:
    """Render the complete game table as ASCII."""
    lines = []
    
    # Title with hand ID
    lines.append("🃏 BLACKJACK 🃏")
    lines.append(f"Hand: #{state.hand_id} | Bet: {state.bet} chips")
    lines.append("")
    
    # Dealer's hand
    lines.append("┌─────────────────────────────────────┐")
    lines.append("│           DEALER'S HAND             │")
    lines.append("└─────────────────────────────────────┘")
    
    if state.dealer_hand.hole_card_hidden and state.phase == "player_turn":
        # Show only upcard during player's turn
        lines.append(render_hand([state.dealer_hand.cards[0]]))
        lines.append(f"Visible: {state.dealer_hand.visible_value}")
        lines.append("(hole card hidden)")
    else:
        # Show full hand after reveal
        lines.append(render_hand(state.dealer_hand.cards))
        lines.append(f"Value: {state.dealer_hand.value}")
    
    lines.append("")
    lines.append("┌─────────────────────────────────────┐")
    lines.append("│            YOUR HAND                │")
    lines.append("└─────────────────────────────────────┘")
    lines.append(render_hand(state.player_hand.cards))
    lines.append(f"Value: {state.player_hand.value}")
    
    if state.player_hand.can_double and state.phase == "player_turn":
        lines.append("(can double)")
    
    lines.append("")
    
    # Status message
    if state.message:
        lines.append(f"► {state.message}")
    
    # Phase-specific instructions
    if state.phase == "player_turn":
        if state.player_hand.can_double:
            lines.append("")
            lines.append("Actions: HIT | STAND | DOUBLE")
        else:
            lines.append("")
            lines.append("Actions: HIT | STAND")
    elif state.phase == "resolved":
        lines.append("")
        lines.append("Hand resolved. Open a new issue to play again.")
    
    return "\n".join(lines)


def render_commitment(state: GameState) -> str:
    """Render the provably fair commitment."""
    if not state.commitment:
        return ""
    
    lines = [
        "🔒 Provably Fair Commitment",
        f"```sha256({state.hand_id[:8]}...)```",
        f"```{state.commitment}```",
    ]
    return "\n".join(lines)


def render_reveal(state: GameState) -> str:
    """Render the full reveal after resolution."""
    if not state.shoe or not state.shoe.nonce:
        return ""
    
    lines = [
        "🔓 Shoe Reveal (verify your hand)",
        f"Nonce: ```{state.shoe.nonce}```",
        f"Commitment verified: {state.shoe.verify_commitment(state.commitment)}",
    ]
    return "\n".join(lines)