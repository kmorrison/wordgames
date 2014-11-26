from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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

class NewLetterForm(forms.Form):
    position = forms.IntegerField()
    letter = forms.CharField(label="New Letter", max_length=1)


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
        return redirect('ghost:landing')
    player1 = _upsert_user(request.user.id)
    player2 = games_models.Player.objects.get(id=form.cleaned_data['other_player_id'])
    game_type = form.cleaned_data['game_type']
    new_ghost_game = logic.GhostLogic.start_game(
        player1,
        player2,
        game_type=game_type,
    )
    return redirect(
        'ghost:game_view',
        ghost_game_id=new_ghost_game.id,
    )

def game_view(request, ghost_game_id):
    ghost_game = get_object_or_404(models.GhostGame, pk=ghost_game_id)
    game_state_presenter = logic.GhostLogic.current_game_state(ghost_game.game_id)

    if request.user.is_active:
        # Find out if the user is playing this game.
        # TODO: Make this a straight join.
        player = games_models.Player.objects.get(
            user_id=request.user.id,
        )
        try:
            game_player = games_models.GamePlayer.objects.get(
                player_id=player.id,
                game_id=ghost_game.game_id,
            )
        except games_models.GamePlayer.DoesNotExist:
            game_player = None

    return render_to_response(
        'ghost/game_view.html',
        dict(
            requesting_game_player=game_player,
            game_state_presenter=game_state_presenter,
            ghost_game_id=ghost_game.id,
        ),
        RequestContext(request),
    )

@login_required
def new_letter_post(request, ghost_game_id):
    ghost_game = get_object_or_404(models.GhostGame, pk=ghost_game_id)
    player = games_models.Player.objects.get(
        user_id=request.user.id,
    )
    try:
        game_player = games_models.GamePlayer.objects.get(
            player_id=player.id,
            game_id=ghost_game.game_id,
        )
    except games_models.GamePlayer.DoesNotExist:
        # The player submitted a guess for a game that wasn't theirs. Naughty.
        # Show them the game they yearn for so badly.
        messages.error(request, "That's not your game!")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    assert request.method == 'POST'
    form = NewLetterForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Something was wrong with your guess. Try again.")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    try:
        logic.GhostLogic.new_guess(
            game_player,
            form.cleaned_data['letter'].upper(),
            form.cleaned_data['position'],
        )
    except logic.InvalidGuessException:
        messages.error(request, "That's not a valid guess. Try again.")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    # TODO: Add opponent name to message.
    messages.info(request, 'You guessed "%s". Now waiting for your opponent.' % (form.cleaned_data['letter'].upper(),))
    return redirect(
        'ghost:game_view',
        ghost_game_id=ghost_game.id,
    )




