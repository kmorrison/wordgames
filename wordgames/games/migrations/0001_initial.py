# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('time_ended', models.DateTimeField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GamePlayer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.IntegerField(null=True)),
                ('has_won', models.BooleanField(default=False)),
                ('game', models.ForeignKey(to='games.Game')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='gameplayer',
            name='player',
            field=models.ForeignKey(to='games.Player'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='game',
            name='players',
            field=models.ManyToManyField(related_name='players', through='games.GamePlayer', to='games.Player'),
            preserve_default=True,
        ),
    ]
