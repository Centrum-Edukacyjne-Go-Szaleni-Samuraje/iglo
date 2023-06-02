from rest_framework import serializers
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework_extensions.routers import ExtendedDefaultRouter

from league.models import Season, Group, Member, Round, Game
import league.igor


class SeasonSerializer(ModelSerializer):
    class Meta:
        model = Season
        fields = [
            "number",
            "start_date",
            "end_date",
            "promotion_count",
            "players_per_group",
            "state",
        ]


class GroupSerializer(ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "name",
            "type",
            "is_egd",
        ]


class MemberSerializer(ModelSerializer):
    player = serializers.CharField(source="player.nick")

    class Meta:
        model = Member
        fields = [
            "id",
            "player",
            "rank",
            "order",
            "final_order",
            "initial_score",
        ]


class RoundSerializer(ModelSerializer):
    class Meta:
        model = Round
        fields = [
            "number",
            "start_date",
            "end_date",
        ]


class GameSerializer(ModelSerializer):
    class Meta:
        model = Game
        fields = [
            "black",
            "white",
            "winner",
            "win_type",
            "points_difference",
            "date",
            "link",
            "sgf",
            "updated",
            "review_video_link",
            "ai_analyse_link",
        ]


class SeasonViewSet(ListModelMixin, RetrieveModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    lookup_field = "number"


class GroupViewSet(ListModelMixin, RetrieveModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    lookup_field = "name"


class MemberViewSet(ListModelMixin, RetrieveModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = Member.objects.all().select_related("player")
    serializer_class = MemberSerializer


class RoundViewSet(ListModelMixin, RetrieveModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = Round.objects.all()
    serializer_class = RoundSerializer
    lookup_field = "number"


class GameViewSet(ListModelMixin, RetrieveModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer


router = ExtendedDefaultRouter()
season_route = router.register("seasons", SeasonViewSet, basename="api-season")
group_route = season_route.register(
    "groups", GroupViewSet, basename="api-seasons-group", parents_query_lookups=["season__number"]
)
group_route.register(
    "members",
    MemberViewSet,
    basename="api-groups-member",
    parents_query_lookups=["group__season__number", "group__name"],
)
group_route.register(
    "rounds",
    RoundViewSet,
    basename="api-groups-round",
    parents_query_lookups=["group__season__number", "group__name"],
).register(
    "games",
    GameViewSet,
    basename="api-rounds-game",
    parents_query_lookups=["group__season__number", "group__name", "round__number"],
)

league.igor.register(router)
