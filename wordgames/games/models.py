from __future__ import absolute_import

from django.db import models
from users.models import User

# Create your models here.
class Player(models.Model):
    # Make user nullable because we might want to have computer players, or
    # guests
    user = models.ForeignKey(User, null=True)

    @property
    def name(self):
        if self.user is not None:
            return self.user.username
        return 'Unknown'

    def __unicode__(self):
        return self.name



class Game(models.Model):
    time_created = models.DateTimeField(auto_now_add=True)
    time_last_activity = models.DateTimeField(
        auto_now_add=True,
        auto_now=True,
    )
    time_ended = models.DateTimeField(null=True)

    players = models.ManyToManyField(
        Player,
        through='GamePlayer',
        related_name='players',
    )


class GamePlayer(models.Model):

    player = models.ForeignKey(Player)
    game = models.ForeignKey(Game)
    score = models.IntegerField(null=True)

    has_won = models.BooleanField(default=False)
    plays_first = models.BooleanField(default=False)
