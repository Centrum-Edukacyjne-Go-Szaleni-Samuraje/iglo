from django.urls import path
from django.views.generic import RedirectView

from league.views import (
    SeasonsListView,
    SeasonDetailView,
    SeasonDeleteView,
    GroupDetailView,
    GroupGamesView,
    GameDetailView,
    PlayerDetailView,
    PlayerUpdateView,
    PrepareSeasonView,
    GameUpdateView,
    SeasonExportCSVView,
    GroupEGDExportView,
    GameDetailRedirectView,
    LeagueAdminView,
    PlayersListView, GameListView, UpcomingGameListView,
)


urlpatterns = [
    path("seasons", SeasonsListView.as_view(), name="seasons-list"),
    path("seasons/prepare", PrepareSeasonView.as_view(), name="seasons-prepare"),
    path("seasons/<int:number>", SeasonDetailView.as_view(), name="season-detail"),
    path("seasons/<int:number>/delete", SeasonDeleteView.as_view(), name="season-delete"),
    path("seasons/<int:number>/export", SeasonExportCSVView.as_view(), name="season-export"),
    path("seasons/<int:season_number>/groups/<group_name>", GroupDetailView.as_view(), name="group-detail"),
    path(
        "seasons/<int:season_number>/<group_name>",
        RedirectView.as_view(permanent=True, pattern_name="group-detail"),
        name="deprecated-group-detail",
    ),
    path("seasons/<int:season_number>/groups/<group_name>/games", GroupGamesView.as_view(), name="group-games"),
    path("seasons/<int:season_number>/groups/<group_name>/egd", GroupEGDExportView.as_view(), name="group-egd-export"),
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
        name="bye-game-detail",
    ),
    path(
        "seasons/<int:season_number>/<group_name>/<bye_player>",
        GameDetailRedirectView.as_view(),
        name="deprecated-bye-game-detail",
    ),
    path(
        "seasons/<int:season_number>/groups/<group_name>/games/<black_player>-<white_player>/edit",
        GameUpdateView.as_view(),
        name="game-update",
    ),
    path("players", PlayersListView.as_view(), name="players-list"),
    path("players/<slug>", PlayerDetailView.as_view(), name="player-detail"),
    path("players/<slug>/settings", PlayerUpdateView.as_view(), name="player-settings"),
    path("league/admin", LeagueAdminView.as_view(), name="league-admin-view"),
    path("games/finished", GameListView.as_view(), name="games-list"),
    path("games/upcoming", UpcomingGameListView.as_view(), name="upcoming-games-list")
]
