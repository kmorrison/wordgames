from django.db import models

from games import models as game_models

class GhostGame(models):
    game = models.ForeignKey(games_models.Game)

# Create your models here.
class NewLetter(models.Model):
    guess_string = models.CharField(max_length=1)
    game = models.ForeignKey(GhostGame)
    player = models.ForeignKey(games_models.Player)
    position = models.IntegerField()
