from __future__ import absolute_import

from django.views.generic.list import ListView

from .models import Game

class GameListView(ListView):

    model = Game

    def get_context_data(self, **kwargs):
        context = super(GameListView, self).get_context_data(**kwargs)
        return context
