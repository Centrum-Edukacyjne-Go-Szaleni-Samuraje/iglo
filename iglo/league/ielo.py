from rest_framework import serializers
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.renderers import JSONRenderer

from league.models import Game, WinType

import accurating
import json


class IeloMatchSerializer(ModelSerializer):
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


def ielo_matches():
    return Game.objects.all().filter(
        win_type__in=[WinType.POINTS, WinType.RESIGN, WinType.TIME]).exclude(winner=None)


class IeloViewSet(ListModelMixin, RetrieveModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = ielo_matches()
    serializer_class = IeloMatchSerializer
    pagination_class = None


def register(router):
    router.register("ielo-matches", IeloViewSet, basename="api-ielo-matches")


# Run shell (README.md) and then:
# from league import ielo; from importlib import reload; reload(ielo);ielo.compute_ar_ratings()
def compute_ar_ratings():
    matches_json = JSONRenderer().render(
        IeloMatchSerializer(ielo_matches(), many=True).data)

    ar_config = accurating.Config(
        season_rating_stability=0.5,
        smoothing=0.1,
        initial_lr=1.0,
        do_log=True,
    )
    print(ar_config)

    matches_dict = json.loads(matches_json)
    print(matches_dict)

    ar_data = accurating.data_from_dicts(matches_dict)
    print(ar_data)

    model = accurating.fit(ar_data, ar_config)
    print(model)
