# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('response', models.CharField(max_length=64)),
                ('game_player', models.ForeignKey(to='games.GamePlayer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GhostGame',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ending_reason', models.CharField(default=b'UKNOWN', max_length=32, choices=[(b'ADJUDICATED', b'Adjudicated'), (b'CHALLENGE_LOST', b'Challenge_Lost'), (b'CHALLENGE_WON', b'Challenge_Won'), (b'RESIGN', b'Resign'), (b'SPELLED', b'Spelled'), (b'UKNOWN', b'Uknown')])),
                ('game_type', models.CharField(default=b'APPEND', max_length=32, choices=[(b'APPEND', b'Append')])),
                ('game', models.ForeignKey(to='games.Game')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewLetter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('guess_string', models.CharField(max_length=1)),
                ('position', models.IntegerField()),
                ('word_after_guess', models.CharField(max_length=64)),
                ('game_player', models.ForeignKey(to='games.GamePlayer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
