from __future__ import absolute_import

from django.conf.urls import patterns
from django.conf.urls import url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.landing, name='landing'),
    url(r'^new_game_post$', views.new_game, name='new_game'),
    url(r'^game/(?P<ghost_game_id>\d+)/$', views.game_view, name='game_view'),
)
