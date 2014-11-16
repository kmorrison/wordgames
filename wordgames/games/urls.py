from __future__ import absolute_import

from django.conf.urls import patterns
from django.conf.urls import url

from .views import GameListView

urlpatterns = patterns('',
    url(r'^$', GameListView.as_view(), name='game-list'),
)
