from __future__ import absolute_import

from django.contrib import admin

from . import models

class GhostGameAdmin(admin.ModelAdmin):
    fields = ['game', 'ending_reason', 'game_type']
    list_display = ['game', 'ending_reason', 'game_type']

admin.site.register(models.GhostGame, GhostGameAdmin)
