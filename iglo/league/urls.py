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
    SeasonExportCSVView,
    GroupEGDExportView,
    GameDetailRedirectView,
    LeagueAdminView,
    PlayersListView,
    GameActionRescheduleView,
    GameActionReportResultView,
    GameActionSubmitReviewView,
)

urlpatterns = [
    path("seasons", SeasonsListView.as_view(), name="seasons-list"),
    path("seasons/prepare", PrepareSeasonView.as_view(), name="seasons-prepare"),
    path("seasons/<int:number>", SeasonDetailView.as_view(), name="season-detail"),
    path("seasons/<int:number>/export", SeasonExportCSVView.as_view(), name="season-export"),
    path("seasons/<int:season_number>/groups/<group_name>", GroupDetailView.as_view(), name="group-detail"),
    path(
        "seasons/<int:season_number>/<group_name>",
        RedirectView.as_view(permanent=True, pattern_name="group-detail"),
        name="deprecated-group-detail",
    ),
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
        "seasons/<int:season_number>/groups/<group_name>/games/<black_player>-<white_player>/reschedule",
        GameActionRescheduleView.as_view(),
        name="game-reschedule",
    ),
    path(
        "seasons/<int:season_number>/groups/<group_name>/games/<black_player>-<white_player>/report-result",
        GameActionReportResultView.as_view(),
        name="game-report-result",
    ),
    path(
        "seasons/<int:season_number>/groups/<group_name>/games/<black_player>-<white_player>/submit-review",
        GameActionSubmitReviewView.as_view(),
        name="game-submit-review",
    ),
    path("players", PlayersListView.as_view(), name="players-list"),
    path("players/<slug>", PlayerDetailView.as_view(), name="player-detail"),
    path("players/<slug>/settings", PlayerUpdateView.as_view(), name="player-settings"),
    path("league/admin", LeagueAdminView.as_view(), name="league-admin-view"),
]
