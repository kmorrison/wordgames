from __future__ import absolute_import

from django.db import models

from enum import Enum

from games import models as game_models

class GameEndingReason(Enum):

    UNKNOWN = 'UKNOWN'
    RESIGN = 'RESIGN'
    CHALLENGE_WON = 'CHALLENGE_WON'
    CHALLENGE_LOST = 'CHALLENGE_LOST'
    ADJUDICATED = 'ADJUDICATED'
    SPELLED = 'SPELLED'

    @classmethod
    def choices(cls):
        return [
            (enum_inst.value, enum_inst.value.title())
            for enum_inst in cls
        ]

class GameType(Enum):

    APPEND = 'APPEND'

    @classmethod
    def choices(cls):
        return [
            (enum_inst.value, enum_inst.value.title())
            for enum_inst in cls
        ]

MAX_WORD_SIZE = 64


class GhostGame(models.Model):
    game = models.ForeignKey(game_models.Game)
    ending_reason = models.CharField(
        max_length=32,
        choices=GameEndingReason.choices(),
        default=GameEndingReason.UNKNOWN.value,
    )
    game_type = models.CharField(
        max_length=32,
        choices=GameType.choices(),
        default=GameType.APPEND.value,
    )


class Challenge(models.Model):
    game_player = models.ForeignKey(game_models.GamePlayer)
    response = models.CharField(max_length=MAX_WORD_SIZE)


class NewLetter(models.Model):
    game_player = models.ForeignKey(game_models.GamePlayer)

    guess_string = models.CharField(max_length=1)
    position = models.IntegerField()
    word_after_guess = models.CharField(max_length=MAX_WORD_SIZE)
