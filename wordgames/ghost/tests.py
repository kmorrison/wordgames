from __future__ import absolute_import

from django.test import TestCase

from games import models as game_models

from . import models
from .logic import GhostLogic
from .logic import InvalidGuessException
from .logic import StaleOperation

# Create your tests here.
class ModelSmokeTestCase(TestCase):

    def setUp(self):
        self.player = game_models.Player()
        self.player.save()

        self.game = game_models.Game()
        self.game.save()

        self.game_player = game_models.GamePlayer(
            game_id=self.game.id,
            player_id=self.player.id,

        )
        self.game_player.save()

    def test_create_ghost_game(self):
        ghost_game = models.GhostGame(
            game_id=self.game.id,
            game_type=models.GameType.APPEND,
        )
        ghost_game.save()

    def test_new_letter_create(self):
        new_letter = models.NewLetter(
            guess_string='a',
            game_player_id=self.game_player.id,
            position=0,
            word_after_guess='a',
        )
        new_letter.save()

    def test_challenge_create(self):
        challenge = models.Challenge(
            game_player_id=self.game_player.id,
        )


class LogicStartGameTestCase(TestCase):

    def setUp(self):
        self.player1 = game_models.Player()
        self.player1.save()
        self.player2 = game_models.Player()
        self.player2.save()

    def test_happy_flow(self):
        ghost_game = GhostLogic.start_game(
            self.player1,
            self.player2,
            first_player_starts_first=True,
        )
        self.assertIsNot(
            ghost_game.id,
            None,
        )
        self.assertEqual(
            models.GameType(ghost_game.game_type),
            models.GameType.APPEND,
        )

        game_player1 = game_models.GamePlayer.objects.get(
            game_id=ghost_game.game_id,
            player_id=self.player1.id,
        )
        self.assertIs(
            game_player1.score,
            None,
        )
        self.assertTrue(game_player1.plays_first)
        self.assertFalse(game_player1.has_won)

        game_player2 = game_models.GamePlayer.objects.get(
            game_id=ghost_game.game_id,
            player_id=self.player2.id,
        )
        self.assertIs(
            game_player2.score,
            None,
        )
        self.assertFalse(game_player2.plays_first)
        self.assertFalse(game_player2.has_won)


class LogicNewGuessTestCase(TestCase):


    def setUp(self):
        self.player1 = game_models.Player()
        self.player1.save()
        self.player2 = game_models.Player()
        self.player2.save()
        self.ghost_game = GhostLogic.start_game(
            self.player1,
            self.player2,
            first_player_starts_first=True,
        )
        self.game_player1 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player1.id,
        )
        self.game_player2 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player2.id,
        )

    def test_happy_flow(self):
        new_letter = GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        self.assertIsNot(
            new_letter.id,
            None,
        )
        self.assertEqual(
            new_letter.guess_string,
            'f',
        )
        self.assertEqual(
            new_letter.word_after_guess,
            'f',
        )

    def test_append(self):
        new_letter = GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        letter_after = GhostLogic.new_guess(
            self.game_player2,
            'o',
            1,
        )
        self.assertEqual(
            letter_after.guess_string,
            'o',
        )
        self.assertEqual(
            letter_after.word_after_guess,
            'fo',
        )

    def test_does_not_move_first(self):
        with self.assertRaises(InvalidGuessException):
            GhostLogic.new_guess(
                self.game_player2,
                'f',
                0,
            )

    def test_move_twice_in_a_row(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        with self.assertRaises(InvalidGuessException):
            GhostLogic.new_guess(
                self.game_player1,
                'f',
                1,
            )

    def test_bad_position(self):
        with self.assertRaises(InvalidGuessException):
            GhostLogic.new_guess(
                self.game_player1,
                'f',
                1,
            )

class LogicIssueChallengeTestCase(TestCase):


    def setUp(self):
        self.player1 = game_models.Player()
        self.player1.save()
        self.player2 = game_models.Player()
        self.player2.save()
        self.ghost_game = GhostLogic.start_game(
            self.player1,
            self.player2,
            first_player_starts_first=True,
        )
        self.game_player1 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player1.id,
        )
        self.game_player2 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player2.id,
        )

    def test_challenge(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        challenge = GhostLogic.issue_challenge(
            self.game_player2,
        )

    def test_challenge_on_first_move(self):
        with self.assertRaises(InvalidGuessException):
            GhostLogic.issue_challenge(
                self.game_player1,
            )

    def test_no_challenge_when_its_not_your_turn(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        with self.assertRaises(InvalidGuessException):
            challenge = GhostLogic.issue_challenge(
                self.game_player1,
            )

    def test_challenge_is_idempotent(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        challenge = GhostLogic.issue_challenge(
            self.game_player2,
        )
        idem_challenge = GhostLogic.issue_challenge(
            self.game_player2,
        )
        self.assertEqual(
            challenge.id,
            idem_challenge.id,
        )
        with self.assertRaises(StaleOperation):
            challenge = GhostLogic.issue_challenge(
                self.game_player1,
            )

class LogicChallengeResponseTestCase(TestCase):

    def setUp(self):
        self.player1 = game_models.Player()
        self.player1.save()
        self.player2 = game_models.Player()
        self.player2.save()
        self.ghost_game = GhostLogic.start_game(
            self.player1,
            self.player2,
            first_player_starts_first=True,
        )
        self.game_player1 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player1.id,
        )
        self.game_player2 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player2.id,
        )

    def test_challenger_loses(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        challenge = GhostLogic.issue_challenge(
            self.game_player2,
        )
        challenge_modified = GhostLogic.respond_to_challenge(
            self.game_player1,
            'fork',
        )
        self.assertEqual(
            challenge.id,
            challenge_modified.id,
        )
        self.assertEqual(
            challenge_modified.response,
            'fork',
        )

        current_game_state = GhostLogic.current_game_state(
            self.ghost_game.game_id,
        )
        self.assertEqual(
            models.GameEndingReason(current_game_state.ending_reason),
            models.GameEndingReason.CHALLENGE_LOST,
        )
        self.assertTrue(current_game_state.is_over)

    def test_challenger_wins(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        challenge = GhostLogic.issue_challenge(
            self.game_player2,
        )
        challenge_modified = GhostLogic.respond_to_challenge(
            self.game_player1,
            'spork',
        )
        self.assertEqual(
            challenge.id,
            challenge_modified.id,
        )
        self.assertEqual(
            challenge_modified.response,
            'spork',
        )

        current_game_state = GhostLogic.current_game_state(
            self.ghost_game.game_id,
        )
        self.assertEqual(
            models.GameEndingReason(current_game_state.ending_reason),
            models.GameEndingReason.CHALLENGE_WON,
        )
        self.assertTrue(current_game_state.is_over)

    def test_word_must_be_long_enough(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        challenge = GhostLogic.issue_challenge(
            self.game_player2,
        )
        challenge_modified = GhostLogic.respond_to_challenge(
            self.game_player1,
            'for',
        )

        current_game_state = GhostLogic.current_game_state(
            self.ghost_game.game_id,
        )
        self.assertEqual(
            models.GameEndingReason(current_game_state.ending_reason),
            models.GameEndingReason.CHALLENGE_WON,
        )

class LogicWordSpelledTestCase(TestCase):
    def setUp(self):
        self.player1 = game_models.Player()
        self.player1.save()
        self.player2 = game_models.Player()
        self.player2.save()
        self.ghost_game = GhostLogic.start_game(
            self.player1,
            self.player2,
            first_player_starts_first=True,
        )
        self.game_player1 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player1.id,
        )
        self.game_player2 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player2.id,
        )

    def test_word_spelled(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        GhostLogic.new_guess(
            self.game_player2,
            'o',
            1,
        )
        GhostLogic.new_guess(
            self.game_player1,
            'r',
            2,
        )
        GhostLogic.new_guess(
            self.game_player2,
            'k',
            3,
        )
        game_state = GhostLogic.word_spelled_accusation(
            self.game_player1,
        )
        self.assertEqual(
            game_state.ending_reason,
            models.GameEndingReason.SPELLED,
        )
        self.assertEqual(
            game_state.winning_player.id,
            self.game_player1.id,
        )

    def test_is_not_a_word(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        GhostLogic.new_guess(
            self.game_player2,
            'o',
            1,
        )
        GhostLogic.new_guess(
            self.game_player1,
            'r',
            2,
        )
        GhostLogic.new_guess(
            self.game_player2,
            'x',
            3,
        )
        game_state = GhostLogic.word_spelled_accusation(
            self.game_player1,
        )
        self.assertEqual(
            game_state.ending_reason,
            models.GameEndingReason.CHALLENGE_LOST,
        )
        self.assertEqual(
            game_state.winning_player.id,
            self.game_player2.id,
        )

class LogicResignTestCase(TestCase):
    def setUp(self):
        self.player1 = game_models.Player()
        self.player1.save()
        self.player2 = game_models.Player()
        self.player2.save()
        self.ghost_game = GhostLogic.start_game(
            self.player1,
            self.player2,
            first_player_starts_first=True,
        )
        self.game_player1 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player1.id,
        )
        self.game_player2 = game_models.GamePlayer.objects.get(
            game_id=self.ghost_game.game_id,
            player_id=self.player2.id,
        )

    def test_resign(self):
        game_state = GhostLogic.resign(self.game_player1)
        self.assertEqual(game_state.winning_player.id, self.game_player2.id)

    def test_can_resign_when_not_your_turn(self):
        game_state = GhostLogic.resign(self.game_player2)
        self.assertEqual(game_state.winning_player.id, self.game_player1.id)

    def test_can_resign_in_challenge_state(self):
        GhostLogic.new_guess(
            self.game_player1,
            'f',
            0,
        )
        GhostLogic.issue_challenge(
            self.game_player2,
        )
        game_state = GhostLogic.resign(self.game_player2)
        self.assertEqual(game_state.winning_player.id, self.game_player1.id)
