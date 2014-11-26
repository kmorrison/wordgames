from __future__ import absolute_import

from collections import namedtuple
import random

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from enum import Enum

from games import models as game_models
from games import logic as game_logic
from words.words import wordlist

from . import models

def assign_random_start():
    return random.random() > 0.5


class InvalidGuessException(Exception):
    pass

class StaleOperation(Exception):
    pass

class StateMachineError(Exception):
    pass


GameStatePresenter = namedtuple('GameStatePresenter', [
    'game_type',
    'game_player_to_move',

    'word_so_far',
    'legal_positions_to_play',

    'is_playing',
    'is_challenge_issued',
    'is_over',
    'ending_reason',
    'winning_player',
])

class PartialWordChecker(object):
    @classmethod
    def one_starts_with_other(cls, partial, whole):
        return whole.lower().startswith(partial.lower())

    @classmethod
    def for_game_type(cls, game_type):
        if game_type == models.GameType.APPEND:
            return cls.one_starts_with_other


class GhostLogic(object):

    @classmethod
    def current_game_state(cls, game_id):
        game = game_models.Game.objects.get(id=game_id)
        ghost_game = models.GhostGame.objects.get(game_id=game_id)

        all_guesses = models.NewLetter.objects.filter(
            game_player__game_id=game_id,
        )

        sorted_guesses = sorted(all_guesses, key=lambda guess: guess.position)
        word_so_far = ''.join([guess.guess_string for guess in sorted_guesses])
        if models.GameType(ghost_game.game_type) == models.GameType.APPEND:
            legal_positions_to_play = [len(word_so_far)]

        game_players = game_models.GamePlayer.objects.filter(
            game_id=game_id,
        ).all()

        possible_challenges = models.Challenge.objects.filter(game_player__game_id=game_id)
        if possible_challenges:
            challenge = possible_challenges[0]
        else:
            challenge = None

        if not all_guesses:
            game_player_to_move, = [game_player for game_player in game_players if game_player.plays_first]
        else:
            most_recent_guess = max(all_guesses, key=lambda guess: guess.id)
            if challenge is None:
                game_player_to_move, = [game_player for game_player in game_players if game_player.id != most_recent_guess.game_player_id]
            else:
                game_player_to_move, = [game_player for game_player in game_players if game_player.id == most_recent_guess.game_player_id]

        if any(game_player.has_won for game_player in game_players):
            winning_player, = [game_player for game_player in game_players if game_player.has_won]
        else:
            winning_player = None


        return GameStatePresenter(
            game_type=models.GameType(ghost_game.game_type),
            game_player_to_move=game_player_to_move,

            word_so_far=word_so_far,
            legal_positions_to_play=legal_positions_to_play,

            is_over=bool(game.time_ended is not None),
            ending_reason=models.GameEndingReason(ghost_game.ending_reason),
            is_challenge_issued=bool(game.time_ended is None) and bool(challenge is not None),
            is_playing=bool(game.time_ended is None) and bool(challenge is None),
            winning_player=winning_player,
        )

    @classmethod
    @transaction.atomic
    def start_game(cls, player1, player2, game_type=models.GameType.APPEND, first_player_starts_first=None):
        if player1.id == player2.id:
            raise AssertionError("Cannot start game with yourself")

        new_game = game_models.Game()
        new_game.save()

        if first_player_starts_first is None:
            first_player_starts_first = assign_random_start()

        game_player1 = game_models.GamePlayer(
            plays_first=first_player_starts_first,
            game_id=new_game.id,
            player_id=player1.id,
            score=None,
            has_won=False,
        )
        game_player1.save()

        game_player2 = game_models.GamePlayer(
            plays_first=not first_player_starts_first,
            game_id=new_game.id,
            player_id=player2.id,
            score=None,
            has_won=False,
        )
        game_player2.save()

        ghost_game = models.GhostGame(
            game_id=new_game.id,
            game_type=game_type.value,
        )
        ghost_game.save()

        return ghost_game

    @classmethod
    def _validate_next_guess_position(cls, game_state, position):
        if position not in game_state.legal_positions_to_play:
            raise InvalidGuessException("Game type %s, legal positions to move %r, received %s" % (
                game_state.game_type,
                game_state.legal_positions_to_play,
                position,
            ))

    @classmethod
    def _validate_player_is_next_to_move(cls, game_state, game_player):
        if game_state.game_player_to_move.id != game_player.id:
            raise InvalidGuessException("It's not that player's turn (GamePlayer:%s)." % (game_player.id))

    @classmethod
    def _validate_is_playing(cls, game_state):
        if not game_state.is_playing:
            raise StaleOperation("Either a challenge has already been issued or the game is over. (Game:%s)" % (game_state.game_player_to_move.game_id,))

    @classmethod
    @transaction.atomic
    def new_guess(cls, game_player, letter, position):
        game_state = cls.current_game_state(game_player.game_id)
        cls._validate_is_playing(
            game_state,
        )
        cls._validate_player_is_next_to_move(
            game_state,
            game_player,
        )
        cls._validate_next_guess_position(
            game_state,
            position,
        )

        new_letter = models.NewLetter(
            game_player_id=game_player.id,
            guess_string=letter,
            position=position,
            word_after_guess=game_state.word_so_far + letter,
        )
        new_letter.save()
        return new_letter

    @classmethod
    @transaction.atomic
    def issue_challenge(cls, game_player):
        if models.Challenge.objects.filter(
            game_player_id=game_player.id,
        ).exists():
            return models.Challenge.objects.get(
                game_player_id=game_player.id,
            )

        game_state = cls.current_game_state(game_player.game_id)
        cls._validate_is_playing(
            game_state,
        )
        cls._validate_player_is_next_to_move(
            game_state,
            game_player,
        )
        if game_state.legal_positions_to_play == [0]:
            raise InvalidGuessException("Cannot challenge on first move. (Game:%s)" % (game_player.game_id,))

        challenge = models.Challenge(
            game_player_id=game_player.id,
        )
        challenge.save()
        return challenge

    @classmethod
    @transaction.atomic
    def respond_to_challenge(cls, game_player, intended_word):
        game_state = cls.current_game_state(game_player.game_id)
        # Idempotence check
        if game_state.is_over:
            try:
                # Have to join because player responding to
                # challenge won't be the one who made it.
                challenge = models.Challenge.objects.get(
                    game_player_id__game_id=game_player.game_id,
                )
                if challenge.response != intended_word:
                    raise StateMachineError(str(game_player.game_id))
                return challenge
            except ObjectDoesNotExist:
                raise StateMachineError(
                    "Responding to challenge, but game:%s ended with %s" % (
                    game_player.game_id,
                    game_state.ending_reason,
                ))

        if not game_state.is_challenge_issued:
            raise StateMachineError("Challenge new issued, cannot respond (Game:%s)" % (game_player.game_id))

        challenge = models.Challenge.objects.get(
            game_player_id__game_id=game_player.game_id,
        )
        challenge.response = intended_word

        responder_wins = bool(
            intended_word in wordlist.wordset
            and PartialWordChecker.for_game_type(
                game_state.game_type
            )(game_state.word_so_far, intended_word)
        )

        if responder_wins:
            game_ending_reason = models.GameEndingReason.CHALLENGE_LOST
            winning_game_player_id = game_player.id
        else:
            game_ending_reason = models.GameEndingReason.CHALLENGE_WON
            winning_game_player_id = game_models.GamePlayer.objects.exclude(
                id=game_player.id
            ).get(game_id=game_player.game_id).id

        ghost_game = models.GhostGame.objects.get(game_id=game_player.game_id)
        ghost_game.ending_reason = game_ending_reason.value
        ghost_game.save()

        game_logic.GamesLogic.end_game(game_player.game_id, winning_game_player_id)

        return challenge
