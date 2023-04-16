from rest_framework import serializers
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework_extensions.routers import ExtendedDefaultRouter

from league.models import Season, Group, Round, Game, WinType

class GameSerializer(ModelSerializer):
    p1 = serializers.CharField(source="black.player.nick")
    p2 = serializers.CharField(source="white.player.nick")
    season = serializers.IntegerField(source="group.season.number")
    weight = serializers.SerializerMethodField()
    winner = serializers.SerializerMethodField()

    def get_winner(self, game):
        if not game.winner: return None
        return game.winner.player.nick

    def get_weight(self, game):
        return {
            WinType.POINTS: 1.0,
            WinType.RESIGN: 1.0,
            WinType.TIME: 1.0,
            WinType.BYE: 0.0,
            # Forfits have less weights onto the ranking.
            WinType.NOT_PLAYED: 0.5,
        }[game.win_type]

    class Meta:
        model = Game
        fields = [
            "p1",
            "p2",
            "winner",
            "date",
            "season",
            "weight",
        ]

class AllGamesViewSet(ListModelMixin, RetrieveModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    pagination_class = None

def register(router):
  router.register("ielo-data", AllGamesViewSet, basename="api-ielo-data")


## MVP
# - [x] Formalize a format for all-the-games and make it into one-call API
# - [ ] Update IELO library to use new JSON format (JSON in, JSON out)
# - [ ] Add ielo_points field and show it in the UI.
# - [ ] Add sort according to the field in a season.
# - [ ] Integrate IELO into IGLO
# - [ ] Populate ielo_points using IELO library.
#
## Extras
#
# - [ ] Make IELO library into a package, add dependency.
# - [ ] Update quick-start instructions in README.md
