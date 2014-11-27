from __future__ import absolute_import
from django.contrib import admin

from . import models

class GameAdmin(admin.ModelAdmin):
    fields = ['time_created', 'time_ended']
    list_display = ['time_created', 'time_ended']

class GamePlayerAdmin(admin.ModelAdmin):
    fields = ['player', 'game', 'has_won']
    list_display = ['player', 'game', 'has_won']


class PlayerAdmin(admin.ModelAdmin):
    fields = ['user']
    list_display = ['user']

admin.site.register(models.Game, GameAdmin)
admin.site.register(models.GamePlayer, GamePlayerAdmin)
admin.site.register(models.Player, PlayerAdmin)
