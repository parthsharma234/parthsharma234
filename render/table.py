"""Retro terminal renderer for GitHub issue comments."""
from engine.game import GameState
from engine.cards import Card


def render_card(card: Card) -> str:
    """Render a compact, ASCII-safe playing card."""
    rank = card.rank.symbol.ljust(2)
    suit = card.suit.value
    return "\n".join([
        "+-------+", f"| {rank}    |", "|       |", f"|   {suit}   |",
        "|       |", f"|    {rank} |", "+-------+",
    ])


def render_hand(cards: list[Card]) -> str:
    if not cards:
        return "(empty)"
    card_lines = [render_card(card).splitlines() for card in cards]
    return "\n".join(" ".join(card[i] for card in card_lines) for i in range(7))


def render_hand_table(state: GameState) -> str:
    """Render the complete table inside a Markdown code block."""
    dealer_hidden = state.dealer_hand.hole_card_hidden and state.phase == "player_turn"
    dealer_cards = [state.dealer_hand.cards[0]] if dealer_hidden else state.dealer_hand.cards
    dealer_value = f"VISIBLE: {state.dealer_hand.visible_value}" if dealer_hidden else f"VALUE: {state.dealer_hand.value}"
    lines = [
        "```text", "+================================================================+",
        "|                  N E O N   B L A C K J A C K                   |",
        f"| HAND #{state.hand_id.upper():<8}  |  WAGER: {state.bet:<4} CHIPS                 |",
        "+================================================================+", "", " DEALER", render_hand(dealer_cards),
        f" {dealer_value}" + ("  [HOLE CARD LOCKED]" if dealer_hidden else ""), "", " PLAYER",
        render_hand(state.player_hand.cards), f" VALUE: {state.player_hand.value}", "",
        "+----------------------------------------------------------------+",
        f"| {state.message[:60]:<62} |", "+----------------------------------------------------------------+",
    ]
    if state.phase == "player_turn":
        actions = "HIT | STAND | DOUBLE" if state.player_hand.can_double else "HIT | STAND"
        lines += [f"| COMMAND: {actions:<51} |", "+================================================================+", "```", "Comment with one command to make your move."]
    else:
        lines += ["| ROUND COMPLETE - open a new issue to play again.              |", "+================================================================+", "```"]
    return "\n".join(lines)


def render_commitment(state: GameState) -> str:
    if not state.commitment:
        return ""
    return "\n".join(["### Fair-deal lock", f"`SHA-256 / hand {state.hand_id[:8]}`", f"`{state.commitment}`", "The full shoe and nonce are revealed after the round."])


def render_reveal(state: GameState) -> str:
    if not state.shoe or not state.shoe.nonce:
        return ""
    verified = "PASS" if state.shoe.verify_commitment(state.commitment) else "FAILED"
    return "\n".join(["### Fair-deal reveal", f"Nonce: `{state.shoe.nonce}`", f"Commitment check: **{verified}**"])
