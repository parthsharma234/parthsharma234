"""Core rules and bankroll regression tests."""
import unittest

from engine.cards import Card, Rank, Suit
from engine.game import BlackjackEngine
from engine.hand import DealerHand, Hand
from engine.player import PlayerState
from engine.shoe import Shoe
from render.table import render_hand_table


class CardAndHandTests(unittest.TestCase):
    def test_card_display_is_terminal_safe(self):
        self.assertEqual(str(Card(Rank.ACE, Suit.HEARTS)), "AH")
        self.assertEqual(str(Card(Rank.TEN, Suit.SPADES)), "10S")

    def test_ace_value_and_blackjack(self):
        hand = Hand()
        hand.add_card(Card(Rank.ACE, Suit.HEARTS))
        hand.add_card(Card(Rank.ACE, Suit.CLUBS))
        hand.add_card(Card(Rank.NINE, Suit.DIAMONDS))
        self.assertEqual(hand.value, 21)
        self.assertFalse(hand.is_blackjack)

    def test_dealer_stands_on_soft_17(self):
        dealer = DealerHand()
        dealer.add_card(Card(Rank.ACE, Suit.HEARTS))
        dealer.add_card(Card(Rank.SIX, Suit.CLUBS))
        self.assertFalse(dealer.should_hit)


class FairShoeTests(unittest.TestCase):
    def test_commitment_survives_deals(self):
        shoe, commitment = Shoe.generate_fresh()
        self.assertEqual(shoe.remaining, 312)
        shoe.deal()
        shoe.deal()
        self.assertTrue(shoe.verify_commitment(commitment))
        self.assertEqual(len(shoe.reveal()["cards"]), 312)


class GameAndBankrollTests(unittest.TestCase):
    def test_start_and_render_hand(self):
        engine = BlackjackEngine()
        state = engine.start_hand("tester", 25, "cafe1234")
        self.assertEqual(len(state.player_hand.cards), 2)
        self.assertIn("N E O N   B L A C K J A C K", render_hand_table(state))

    def test_double_doubles_the_wager_and_finishes(self):
        engine = BlackjackEngine()
        engine.start_hand("tester", 25, "double01")
        engine.double()
        self.assertEqual(engine.state.bet, 50)
        self.assertEqual(len(engine.state.player_hand.cards), 3)
        self.assertEqual(engine.state.phase, "resolved")

    def test_held_wager_is_returned_on_push(self):
        player = PlayerState(username="tester")
        engine = BlackjackEngine()
        state = engine.start_hand("tester", 25, "push0001")
        player.start_hand(state, 25)
        state.player_hand.result = "push"
        state.player_hand.payout = 0
        player.resolve_hand(0, "push")
        self.assertEqual(player.chips, 1000)

    def test_win_credits_wager_plus_profit(self):
        player = PlayerState(username="tester")
        engine = BlackjackEngine()
        state = engine.start_hand("tester", 25, "win00001")
        player.start_hand(state, 25)
        state.player_hand.result = "win"
        state.player_hand.payout = 25
        player.resolve_hand(25, "win")
        self.assertEqual(player.chips, 1025)

    def test_loss_does_not_return_wager(self):
        player = PlayerState(username="tester")
        engine = BlackjackEngine()
        state = engine.start_hand("tester", 25, "lose0001")
        player.start_hand(state, 25)
        state.player_hand.result = "lose"
        state.player_hand.payout = -25
        player.resolve_hand(-25, "lose")
        self.assertEqual(player.chips, 975)


if __name__ == "__main__":
    unittest.main()
