from rest_framework import serializers
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from league.models import Game, WinType


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
