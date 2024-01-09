from rest_framework import serializers
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.renderers import JSONRenderer
from rest_framework_extensions.routers import ExtendedDefaultRouter

from django.conf import settings
from league.models import Game, WinType, Player

import accurating
import json


class IgorMatchSerializer(ModelSerializer):
    p1 = serializers.CharField(source="black.player.nick")
    p2 = serializers.CharField(source="white.player.nick")
    season = serializers.IntegerField(source="group.season.number")
    winner = serializers.CharField(source="winner.player.nick")

    class Meta:
        model = Game
        fields = [
            "p1",
            "p2",
            "winner",
            "season",
        ]


def igor_matches():
    return (
        Game.objects.all()
        .filter(win_type__in=[WinType.POINTS, WinType.RESIGN, WinType.TIME])
        .exclude(winner=None)
        .select_related("black__player", "white__player", "group__season", "winner__player")
    )


class IgorViewSet(ListModelMixin, RetrieveModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = igor_matches()
    serializer_class = IgorMatchSerializer
    pagination_class = None


def register(router: ExtendedDefaultRouter):
    router.register("igor-matches", IgorViewSet, basename="api-igor-matches")


def recalculate_igor():

    ar_config = accurating.Config(**settings.IGOR_CONFIG)

    matches = [
        dict(
            p1=game.black.player.nick,
            p2=game.white.player.nick,
            season=game.group.season.number - 1,  # For internal datastructure we index seasons from 0
            winner=game.winner.player.nick,
        ) for game in igor_matches()
    ]
    # The above code is equivalent to:
    # matches_json = JSONRenderer().render(IgorMatchSerializer(igor_matches(), many=True).data)
    # matches = json.loads(matches_json)
    ar_data = accurating.data_from_dicts(matches)
    model = accurating.fit(ar_data, ar_config)

    to_update = Player.objects.filter(nick__in=model.rating.keys())
    for player in to_update:
        if player.nick in model.rating:
            memberships = player.memberships.select_related("group__season")
            participated_seasons = {m.group.season.number - 1 for m in memberships} # index seasons from 0

            def get_rating(kv):
                season, rating = kv
                return rating if season in participated_seasons else None

            pratings = model.rating[player.nick]
            pratings = sorted(pratings.items())
            pratings = list(map(get_rating, pratings))
            player.igor_history = pratings
            if len(pratings) > 0:
                player.igor = pratings[-1]

            # Useful when testing from `manage.py shell` (PTAL README.md):
            # print("player.nick = ", player.nick)
            # print("participated_seasons = ", participated_seasons)
            # print("player.igor_history = ", player.igor_history)
            # print()

    Player.objects.bulk_update(to_update, fields=['igor', 'igor_history'])
