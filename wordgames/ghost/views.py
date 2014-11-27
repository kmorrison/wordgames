from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext

from games import logic as games_logic
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
    player = forms.ChoiceField(
        choices=[(player.id, player.name) for player in games_models.Player.objects.all()],
    )
    game_type = forms.TypedChoiceField(
        choices=models.GameType.choices(),
        coerce=models.GameType,
    )

class NewLetterForm(forms.Form):
    position = forms.IntegerField()
    letter = forms.CharField(label="New Letter", max_length=1)


class RespondToChallengeForm(forms.Form):
    response = forms.CharField(label="New Letter", max_length=64)


def _load_player_for_game(request, ghost_game):
    player = games_models.Player.objects.get(
        user_id=request.user.id,
    )
    try:
        return games_models.GamePlayer.objects.get(
            player_id=player.id,
            game_id=ghost_game.game_id,
        )
    except games_models.GamePlayer.DoesNotExist:
        return None


def landing(request):
    player = None

    # This write-on-get is super dirty. Replace it with signals on the user
    # sign-up.
    if request.user.is_active:
        player = _upsert_user(request.user.id)

    latest_game_states = logic.GhostLogic.latest_games(n=20)

    response = dict(
        player=player,
        latest_game_states=latest_game_states,
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
    player2 = games_models.Player.objects.get(id=form.cleaned_data['player'])
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
        try:
            player = games_models.Player.objects.get(
                user_id=request.user.id,
            )
            game_player = games_models.GamePlayer.objects.get(
                player_id=player.id,
                game_id=ghost_game.game_id,
            )
        except (games_models.Player.DoesNotExist, games_models.GamePlayer.DoesNotExist):
            game_player = None

    if game_state_presenter.winning_player is not None:
        winning_player = games_logic.GamesLogic.load_player(game_state_presenter.winning_player.id)
    else:
        winning_player = None
    return render_to_response(
        'ghost/game_view.html',
        dict(
            requesting_game_player=game_player,
            game_state_presenter=game_state_presenter,
            ghost_game_id=ghost_game.id,
            winning_player=winning_player,
        ),
        RequestContext(request),
    )

@login_required
def new_letter_post(request, ghost_game_id):
    ghost_game = get_object_or_404(models.GhostGame, pk=ghost_game_id)
    game_player = _load_player_for_game(request, ghost_game)
    if game_player is None:
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
            form.cleaned_data['letter'].lower(),
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

@login_required
def challenge(request, ghost_game_id):
    # TODO: Dry this up
    ghost_game = get_object_or_404(models.GhostGame, pk=ghost_game_id)
    game_player = _load_player_for_game(request, ghost_game)
    if game_player is None:
        # The player submitted a guess for a game that wasn't theirs. Naughty.
        # Show them the game they yearn for so badly.
        messages.error(request, "That's not your game!")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    assert request.method == 'POST'
    try:
        logic.GhostLogic.issue_challenge(
            game_player,
        )
    except (logic.InvalidGuessException, logic.StaleOperation, logic.StateMachineError):
        messages.error(request, "Can't do that right now, sorry.")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    game_state_presenter = logic.GhostLogic.current_game_state(ghost_game.game_id)
    messages.info(request, "Waiting for your opponent to tell us what they will spell with %s" % (game_state_presenter.word_so_far.upper(),))
    return redirect(
        'ghost:game_view',
        ghost_game_id=ghost_game.id,
    )

@login_required
def challenge_respond(request, ghost_game_id):
    ghost_game = get_object_or_404(models.GhostGame, pk=ghost_game_id)
    game_player = _load_player_for_game(request, ghost_game)
    if game_player is None:
        # The player submitted a guess for a game that wasn't theirs. Naughty.
        # Show them the game they yearn for so badly.
        messages.error(request, "That's not your game!")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )
    form = RespondToChallengeForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Something wrong with your response. Try again.")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    try:
        challenge = logic.GhostLogic.respond_to_challenge(
            game_player,
            form.cleaned_data['response'].lower(),
        )
    except (logic.InvalidGuessException, logic.StaleOperation, logic.StateMachineError):
        messages.error(request, "Can't do that right now. Sorry.")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    game_state_presenter = logic.GhostLogic.current_game_state(ghost_game.game_id)
    if game_state_presenter.ending_reason == models.GameEndingReason.CHALLENGE_LOST:
        messages.success(request, 'You won! "%s" is a sweet word' % (challenge.response.upper(),))
    elif game_state_presenter.ending_reason == models.GameEndingReason.CHALLENGE_WON:
        messages.error(request, 'You lost! "%s" not a word, according to our databases.' % (challenge.response.upper(),))

    return redirect(
        'ghost:game_view',
        ghost_game_id=ghost_game.id,
    )

@login_required
def word_spelled_post(request, ghost_game_id):
    # TODO: Dry this up
    ghost_game = get_object_or_404(models.GhostGame, pk=ghost_game_id)
    game_player = _load_player_for_game(request, ghost_game)
    if game_player is None:
        # The player submitted a guess for a game that wasn't theirs. Naughty.
        # Show them the game they yearn for so badly.
        messages.error(request, "That's not your game!")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    assert request.method == 'POST'
    try:
        game_state_presenter = logic.GhostLogic.word_spelled_accusation(
            game_player,
        )
    except (logic.InvalidGuessException, logic.StaleOperation, logic.StateMachineError):
        messages.error(request, "Can't do that right now, sorry.")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    if game_state_presenter.ending_reason == models.GameEndingReason.CHALLENGE_LOST:
        messages.error(request, 'You lost! "%s" not a word, according to our databases.' % (game_state_presenter.word_so_far.upper(),))
    elif game_state_presenter.ending_reason == models.GameEndingReason.SPELLED:
        messages.success(request, 'You won! "%s" was a word.' % (game_state_presenter.word_so_far.upper(),))
    return redirect(
        'ghost:game_view',
        ghost_game_id=ghost_game.id,
    )


@login_required
def resign_post(request, ghost_game_id):
    # TODO: Dry this up
    ghost_game = get_object_or_404(models.GhostGame, pk=ghost_game_id)
    game_player = _load_player_for_game(request, ghost_game)
    if game_player is None:
        # The player submitted a guess for a game that wasn't theirs. Naughty.
        # Show them the game they yearn for so badly.
        messages.error(request, "That's not your game!")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    assert request.method == 'POST'
    try:
        game_state_presenter = logic.GhostLogic.resign(
            game_player,
        )
    except (logic.InvalidGuessException, logic.StaleOperation, logic.StateMachineError):
        messages.error(request, "Can't do that right now, sorry.")
        return redirect(
            'ghost:game_view',
            ghost_game_id=ghost_game.id,
        )

    if game_state_presenter.ending_reason == models.GameEndingReason.RESIGN:
        messages.info(request, 'You resigned. Better luck next time')
    return redirect(
        'ghost:game_view',
        ghost_game_id=ghost_game.id,
    )
