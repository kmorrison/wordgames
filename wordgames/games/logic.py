from __future__ import absolute_import

from django.utils import timezone

from . import models

class GamesLogic(object):

    @classmethod
    def end_game(cls, game_id, winning_game_player_id):
        game = models.Game.objects.get(id=game_id)
        game.time_ended = timezone.now()
        game.save()

        game_player = models.GamePlayer.objects.get(
            id=winning_game_player_id,
        )
        game_player.has_won = True
        game_player.save()
