from django.urls import path
from django.views.generic import RedirectView

from league.views import (
    SeasonsListView,
    SeasonDetailView,
    GroupDetailView,
    GameDetailView,
    PlayerDetailView,
    PlayerUpdateView,
    PrepareSeasonView,
    GameUpdateView,
    SeasonExportCSVView,
    GroupEGDExportView,
    GameDetailRedirectView,
)

urlpatterns = [
    path("seasons", SeasonsListView.as_view(), name="seasons-list"),
    path("seasons/prepare", PrepareSeasonView.as_view(), name="seasons-prepare"),
    path("seasons/<int:number>", SeasonDetailView.as_view(), name="season-detail"),
    path("seasons/<int:number>/export", SeasonExportCSVView.as_view(), name="season-export"),
    path(
        "seasons/<int:season_number>/groups/<group_name>",
        GroupDetailView.as_view(),
        name="group-detail"),
    path(
        "seasons/<int:season_number>/<group_name>",
        RedirectView.as_view(permanent=True, pattern_name="group-detail"),
        name="deprecated-group-detail"
    ),
    path(
        "seasons/<int:season_number>/groups/<group_name>/egd",
        GroupEGDExportView.as_view(),
        name="group-egd-export"),
    path(
        "seasons/<int:season_number>/<group_name>/egd",
        RedirectView.as_view(permanent=True, pattern_name="group-egd-export"),
        name="deprecated-group-egd-export"),
    path(
        "seasons/<int:season_number>/groups/<group_name>/games/<black_player>-<white_player>",
        GameDetailView.as_view(),
        name="game-detail",
    ),
    path(
        "seasons/<int:season_number>/<group_name>/<black_player>-<white_player>",
        GameDetailRedirectView.as_view(),
        name="deprecated-game-detail",
    ),
    path(
        "seasons/<int:season_number>/groups/<group_name>/games/<bye_player>",
        GameDetailView.as_view(),
        name="bye-game-detail"
    ),
    path(
        "seasons/<int:season_number>/<group_name>/<bye_player>",
        GameDetailRedirectView.as_view(),
        name="deprecated-bye-game-detail"),
    path(
        "seasons/<int:season_number>/groups/<group_name>/games/<black_player>-<white_player>/edit",
        GameUpdateView.as_view(),
        name="game-update",
    ),
    path(
        "seasons/<int:season_number>/<group_name>/<black_player>-<white_player>/edit",
        RedirectView.as_view(permanent=True, pattern_name="game-update"),
        name="deprecated-game-update",
    ),
    path("players/<slug>", PlayerDetailView.as_view(), name="player-detail"),
    path("players/<slug>/settings", PlayerUpdateView.as_view(), name="player-settings"),
]
