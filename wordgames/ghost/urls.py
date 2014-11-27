from __future__ import absolute_import

from django.conf.urls import patterns
from django.conf.urls import url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.landing, name='landing'),
    url(r'^new_game_post$', views.new_game, name='new_game'),
    url(r'^game/(?P<ghost_game_id>\d+)/$', views.game_view, name='game_view'),
    url(r'^game/(?P<ghost_game_id>\d+)/new_letter$', views.new_letter_post, name='new_letter'),
    url(r'^game/(?P<ghost_game_id>\d+)/challenge$', views.challenge, name='challenge'),
    url(r'^game/(?P<ghost_game_id>\d+)/word_spelled$', views.word_spelled_post, name='word_spelled'),
    url(r'^game/(?P<ghost_game_id>\d+)/respond$', views.challenge_respond, name='respond'),
    url(r'^game/(?P<ghost_game_id>\d+)/resign$', views.resign_post, name='resign'),
)
