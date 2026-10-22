from django.http import Http404
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework_extensions.routers import ExtendedDefaultRouter

from league.models import Season, SeasonState, Group, Member, Round, Game
from league.services.season_report import SeasonReportService
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
            "kifubara_link",
        ]


class SeasonViewSet(ListModelMixin, RetrieveModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    lookup_field = "number"

    def get_season_object(self, lookup_value: str) -> Season:
        if lookup_value == "latest":
            season = (
                Season.objects.exclude(state=SeasonState.DRAFT)
                .order_by("-number")
                .first()
            )
            if not season:
                try:
                    season = Season.objects.get_latest()
                except Season.DoesNotExist:
                    raise Http404("No seasons found")
            return season

        season = Season.objects.filter(number=lookup_value).first()
        if not season and lookup_value.isdigit():
            season = Season.objects.filter(pk=lookup_value).first()
        if not season:
            raise Http404(f"Season '{lookup_value}' not found")
        return season

    @action(detail=True, methods=["get"], url_path="report")
    def report(self, request, number=None):
        season = self.get_season_object(number)
        return Response(SeasonReportService.generate_report(season))

    @action(detail=False, methods=["get"], url_path="latest/report")
    def latest_report(self, request):
        season = self.get_season_object("latest")
        return Response(SeasonReportService.generate_report(season))


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
