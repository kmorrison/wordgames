from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext

from games import models as games_models
from . import models
from . import logic

def _upsert_user(user_id):
    player, _ = games_models.Player.objects.get_or_create(
        user_id=user_id,
    )
    # TODO: Return ongoing games
    return player

class NewGameForm(forms.Form):
    other_player_id = forms.IntegerField()
    game_type = forms.TypedChoiceField(
        choices=models.GameType.choices(),
        coerce=models.GameType,
    )


def landing(request):
    player = None
    current_games = []
    if request.user.is_active:
        player = _upsert_user(request.user.id)

    response = dict(
        player=player,
        current_games=current_games,
        new_game_form=NewGameForm(),
    )
    return render_to_response(
        'ghost/landing.html',
        response,
        RequestContext(request),
    )

@login_required
def new_game(request):
    assert request.method == 'POST'
    form = NewGameForm(request.POST)
    if not form.is_valid():
        return redirect('landing')
    player1 = _upsert_user(request.user.id)
    player2 = games_models.Player.objects.get(id=form.cleaned_data['other_player_id'])
    game_type = form.cleaned_data['game_type']
    new_ghost_game = logic.GhostLogic.start_game(
        player1,
        player2,
        game_type=game_type,
    )
    return redirect('game_view', ghost_game_id=new_ghost_game.id)

def game_view(request, ghost_game_id):
    ghost_game = get_object_or_404(models.GhostGame, pk=ghost_game_id)
    game = games_models.Game.objects.get(id=ghost_game.id)
    return render_to_response(
        'ghost/game_view.html',
        dict(hello="hi"),
    )


