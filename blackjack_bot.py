"""Blackjack bot - GitHub issue interaction."""
import os
import sys
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from engine.game import BlackjackEngine, GameAction
from engine.player import PlayerState, StatsManager
from engine.hand_storage import CompletedHand
from render.table import render_hand_table, render_commitment, render_reveal

import requests


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY", "parthsharma234/parthsharma234")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER")
EVENT_NAME = os.environ.get("EVENT_NAME", "issues")
# Get content from workflow - prefer these over API calls
COMMENT_BODY = os.environ.get("COMMENT_BODY", "")
ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")


def get_issue_comment() -> str:
    """Get the issue body or comment body."""
    # Use workflow-provided values first
    if COMMENT_BODY:
        return COMMENT_BODY
    
    # For new issues, use title/body
    if ISSUE_BODY:
        return f"{ISSUE_TITLE}\n{ISSUE_BODY}"
    
    if not GITHUB_TOKEN or not ISSUE_NUMBER:
        return ""
    
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        if EVENT_NAME == "issues":
            return data.get("body", "")
        else:
            # For comments, get the latest comment
            comments_url = data.get("comments_url")
            comments_resp = requests.get(comments_url, headers=headers)
            comments = comments_resp.json()
            if comments:
                return comments[-1].get("body", "")
        return ""
    except Exception as e:
        print(f"Error fetching issue: {e}")
        return ""


def parse_bet(text: str) -> Optional[int]:
    """Parse bet amount from issue body or comment."""
    # Match "bet: 25" or "bet:25" case insensitive
    match = re.search(r"bet:\s*(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def parse_action(text: str) -> Optional[str]:
    """Parse player action from comment."""
    text_lower = text.lower().strip()
    
    if text_lower in ("hit", "stand", "double"):
        return text_lower
    
    # Also check for explicit commands
    if re.search(r"\bhit\b", text_lower):
        return "hit"
    if re.search(r"\bstand\b", text_lower):
        return "stand"
    if re.search(r"\bdouble\b", text_lower):
        return "double"
    
    return None


def get_username() -> str:
    """Get the username from the issue author."""
    if not GITHUB_TOKEN or not ISSUE_NUMBER:
        return "test_player"
    
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("user", {}).get("login", "unknown")
    except:
        return "test_player"


def get_bot_comment_id() -> Optional[int]:
    """Find the bot's existing comment to edit."""
    if not GITHUB_TOKEN or not ISSUE_NUMBER:
        return None
    
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    try:
        # Get the GitHub token's owner (bot)
        me_url = "https://api.github.com/user"
        me_resp = requests.get(me_url, headers=headers)
        bot_login = me_resp.json().get("login", "")
        
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        comments = resp.json()
        
        for comment in comments:
            if comment.get("user", {}).get("login") == bot_login:
                return comment.get("id")
    except Exception as e:
        print(f"Error finding bot comment: {e}")
    
    return None


def post_or_edit_comment(body: str, comment_id: Optional[int] = None) -> None:
    """Post a new comment or edit an existing one."""
    if not GITHUB_TOKEN or not ISSUE_NUMBER:
        # Debug mode - just print
        print("\n" + "="*50)
        print("BOT RESPONSE:")
        print("="*50)
        print(body)
        print("="*50 + "\n")
        return
    
    url = f"https://api.github.com/repos/{REPO}/issues/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    try:
        if comment_id:
            # Edit existing comment
            edit_url = f"{url}/{comment_id}"
            resp = requests.patch(edit_url, headers=headers, json={"body": body})
            resp.raise_for_status()
        else:
            # Post new comment
            issue_url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
            resp = requests.post(issue_url, headers=headers, json={"body": body})
            resp.raise_for_status()
    except Exception as e:
        print(f"Error posting comment: {e}")
        sys.exit(1)


def close_issue() -> None:
    """Close the issue after hand resolves."""
    if not GITHUB_TOKEN or not ISSUE_NUMBER:
        return
    
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    try:
        resp = requests.patch(url, headers=headers, json={"state": "closed"})
        resp.raise_for_status()
    except Exception as e:
        print(f"Error closing issue: {e}")


def generate_hand_id() -> str:
    """Generate a unique hand ID."""
    import secrets
    return secrets.token_hex(4)


def update_readme(player: Optional[PlayerState] = None, last_hand: Optional[dict] = None) -> None:
    """Update README.md with current casino floor state."""
    readme_path = Path("README.md")
    stats = StatsManager()
    
    # Build leaderboard
    players_dir = Path("players")
    leaderboard = []
    
    if players_dir.exists():
        for pf in players_dir.glob("*.json"):
            with open(pf) as f:
                data = json.load(f)
                leaderboard.append({
                    "username": data.get("username", ""),
                    "chips": data.get("chips", 0),
                    "streak": data.get("current_streak", 0),
                    "hands": data.get("hands_played", 0),
                })
    
    # Sort by chips descending
    leaderboard.sort(key=lambda x: x["chips"], reverse=True)
    leaderboard = leaderboard[:10]  # Top 10
    
    # Load last hand
    hands_dir = Path("hands")
    last_hand_data = None
    if hands_dir.exists():
        hands = list(hands_dir.glob("*.json"))
        if hands:
            # Get most recent
            hands.sort(key=lambda p: Path(p).stat().st_mtime, reverse=True)
            with open(hands[0]) as f:
                last_hand_data = json.load(f)
    
    # Build leaderboard table
    if leaderboard:
        lb_rows = []
        for p in leaderboard:
            lb_rows.append(f"| {p['username']} | {p['chips']} | {p['streak']} | {p['hands']} |")
        leaderboard_table = "\n".join(lb_rows)
    else:
        leaderboard_table = "| — | — | — | — |"
    
    # Build house stats
    stats_dict = stats.to_dict()
    house_stats = f"""- **Total Hands:** {stats_dict['total_hands']}
- **Unique Players:** {stats_dict['unique_players']}
- **Chips Won:** {stats_dict['chips_won']}
- **Chips Lost:** {stats_dict['chips_lost']}
- **Biggest Win:** {stats_dict['biggest_win']}
- **Longest Streak:** {stats_dict['longest_streak']}
- **House Edge:** {stats_dict['house_edge_realized']}% (theoretical: 0.5%)"""
    
    # Last hand section
    if last_hand_data:
        last_hand_section = f"""**{last_hand_data['player']}** bet {last_hand_data['bet']}: {last_hand_data['result']} ({last_hand_data['payout']:+d} chips)"""
    else:
        last_hand_section = "*No hands played yet.*"
    
    # Read current README
    with open(readme_path) as f:
        content = f.read()
    
    # Replace casino section
    casino_section = f"""<!-- BLACKJACK_CASINO_START -->
🃏 **Casino Floor** 🃏

*[Deal me in →](https://github.com/{REPO}/issues/new?title=blackjack&body=bet%3A+25)*

### Leaderboard

| Player | Chips | Streak | Hands Played |
|--------|-------|--------|--------------|
{leaderboard_table}

*No players yet. Be the first!*

### House Stats

{house_stats}

### Last Hand

{last_hand_section}

### Verification

To verify a hand's provably fair commitment:

```python
import hashlib
import json

# After hand resolves, get nonce and full shoe from hands/<id>.json
# Compute: hashlib.sha256((nonce + json.dumps(shoe, sort_keys=True)).hexdigest())
# Compare to the commitment shown during play
```
<!-- BLACKJACK_CASINO_END -->"""
    
    # Use regex to replace the section
    import re
    pattern = r"<!-- BLACKJACK_CASINO_START -->.*?<!-- BLACKJACK_CASINO_END -->"
    content = re.sub(pattern, casino_section, content, flags=re.DOTALL)
    
    with open(readme_path, "w") as f:
        f.write(content)


def main():
    """Main bot entry point."""
    # Get issue/comment content
    text = get_issue_comment()
    username = get_username()
    comment_id = get_bot_comment_id()
    
    # Load player state
    player = PlayerState.load(username)
    
    # Check for existing active hand
    if player.active_hand and player.active_hand.phase != "resolved":
        # Resume existing hand
        engine = BlackjackEngine()
        engine.state = player.active_hand
        
        # Parse action from comment
        action = parse_action(text)
        
        if not action:
            # Invalid action - show current state with error
            response = render_hand_table(engine.state)
            response += "\n\n⚠️ Invalid action. Use: HIT, STAND, or DOUBLE"
            post_or_edit_comment(response, comment_id)
            return
        
        # Execute action
        if action == "hit":
            engine.hit()
        elif action == "stand":
            engine.stand()
        elif action == "double":
            engine.double()
        
        # Update player state
        player.active_hand = engine.state
        
        if engine.state.phase == "resolved":
            # Hand complete - resolve
            result = engine.state.player_hand.result
            payout = engine.state.player_hand.payout
            
            player.resolve_hand(payout, result)
            
            # Record to stats
            stats = StatsManager()
            stats.record_hand(username, payout, player.current_streak)
            
            # Save completed hand
            if engine.state.shoe:
                reveal = engine.state.shoe.reveal()
                hand = CompletedHand(
                    hand_id=engine.state.hand_id,
                    player=username,
                    bet=engine.state.bet,
                    player_cards=[c.to_dict() for c in engine.state.player_hand.cards],
                    dealer_cards=[c.to_dict() for c in engine.state.dealer_hand.cards],
                    player_value=engine.state.player_hand.value,
                    dealer_value=engine.state.dealer_hand.value,
                    result=result,
                    payout=payout,
                    nonce=reveal["nonce"],
                    commitment=engine.state.commitment,
                    timestamp=datetime.utcnow().isoformat(),
                )
                hand.save()
            
            # Update README
            update_readme()
            
            # Show final state with reveal
            response = render_hand_table(engine.state)
            response += "\n\n" + render_reveal(engine.state)
            
            post_or_edit_comment(response, comment_id)
            close_issue()
        else:
            # Hand continues
            player.save()
            
            response = render_hand_table(engine.state)
            response += "\n\n" + render_commitment(engine.state)
            
            post_or_edit_comment(response, comment_id)
    else:
        # New hand
        bet = parse_bet(text)
        
        if not bet:
            # No bet - show instructions
            response = """🃏 Welcome to Blackjack!

To start a new hand, add your bet in the issue body or comment:

```
bet: 25
```

**Bet options:** 25, 50, 100, 250 chips

Starting chips: 1,000

Rules:
- Dealer stands on all 17
- Blackjack pays 3:2
- Double allowed on first two cards only
- No splits or insurance

When your hand starts, comment HIT, STAND, or DOUBLE to play."""
            post_or_edit_comment(response, comment_id)
            return
        
        if bet not in BlackjackEngine.BET_PRESETS:
            response = f"⚠️ Invalid bet. Choose from: {BlackjackEngine.BET_PRESETS}"
            post_or_edit_comment(response, comment_id)
            return
        
        if not player.can_play(bet):
            response = f"⚠️ Cannot play: insufficient chips ({player.chips}) or active hand in progress"
            post_or_edit_comment(response, comment_id)
            return
        
        # Start new hand
        hand_id = generate_hand_id()
        engine = BlackjackEngine()
        state = engine.start_hand(username, bet, hand_id)
        
        # Save player state
        player.start_hand(state, bet)
        player.save()
        
        # Render response
        response = render_hand_table(state)
        response += "\n\n" + render_commitment(state)
        
        post_or_edit_comment(response, comment_id)


if __name__ == "__main__":
    main()