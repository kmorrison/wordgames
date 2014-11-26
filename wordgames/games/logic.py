from __future__ import absolute_import

from collections import namedtuple

from django.utils import timezone

from . import models

PlayerPresenter = namedtuple('PlayerPresenter', [
    'id',
    'name',
])


class GamesLogic(object):

    @classmethod
    def create_player_for_user(cls, user):
        models.Player(
            user_id=user.id,
        ).save()

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

    @classmethod
    def load_player(cls, game_player_id):
        game_player = models.GamePlayer.objects.select_related('player.user').get(id=game_player_id)
        user = game_player.player.user
        if user is not None:
            name = user.username
        else:
            name = ''
        return PlayerPresenter(id=game_player.player_id, name=name)

